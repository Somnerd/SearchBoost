use axum::{routing::{get, post}, Json, Router, extract::{State, Path}, response::IntoResponse, http::StatusCode};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use deadpool_redis::redis::AsyncCommands;
use std::collections::HashMap;
use tower_governor::{governor::GovernorConfigBuilder, GovernorLayer};
use crate::Warden;
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Deserialize)]
pub struct SearchRequest {
    pub query: String,
    pub thread_id: String,
    pub username: String,
    pub options: Option<HashMap<String, serde_json::Value>>,
}

#[derive(Deserialize)]
pub struct ResultParams {
    pub username: String,
}

pub async fn start_relay(port: u16, warden: Arc<Warden>) {
    let governor_conf = Arc::new(
        GovernorConfigBuilder::default()
            .per_second(25)
            .burst_size(100)
            .finish()
            .expect("FATAL: Failed to initialize Governor Rate Limiter"), // Acceptable startup panic
    );

    let app = Router::new()
        .route("/health", get(handle_health))
        .route("/enqueue", post(handle_enqueue))
        .route("/results/:job_id", get(handle_get_result))
        .layer(GovernorLayer { config: governor_conf })
        .with_state(warden);

    let addr = format!("{ip}:{port}", ip="0.0.0.0", port=port);
    let listener = tokio::net::TcpListener::bind(&addr).await.expect("FATAL: Cannot bind to relay port");
    tracing::info!("Relay Module listening on {address} [IDOR Protected]", address=addr);
    axum::serve(listener, app.into_make_service_with_connect_info::<std::net::SocketAddr>()).await.expect("FATAL: Relay server crashed");
}

async fn handle_enqueue(
    State(warden): State<Arc<Warden>>,
    Json(payload): Json<SearchRequest>,
) -> impl IntoResponse {
    if !warden.breaker.is_call_permitted() {
        return (StatusCode::SERVICE_UNAVAILABLE, "Circuit Breaker is OPEN").into_response();
    }

    // 🛡️ IDOR Protection: Self-Sovereign check via metadata DB
    let thread_exists: Result<bool, sqlx::Error> = sqlx::query_scalar::<_, bool>(
        "SELECT EXISTS(SELECT 1 FROM threads t JOIN users u ON t.user_id = u.id WHERE t.id::text = $1 AND u.username = $2)"
    )
    .bind(&payload.thread_id)
    .bind(&payload.username)
    .fetch_one(&warden.db_pool)
    .await;

    match thread_exists {
        Ok(true) => {}, // Validated
        Ok(false) => {
            tracing::warn!("Blocked IDOR Attempt: {} tried to access thread {}", payload.username, payload.thread_id);
            return (StatusCode::FORBIDDEN, "Thread access denied").into_response();
        },
        Err(e) => {
            tracing::error!("Database query failed during IDOR check: {}", e);
            warden.breaker.on_error();
            return (StatusCode::SERVICE_UNAVAILABLE, "Authorization layer unavailable").into_response();
        }
    }

    let session_id = format!("SB-SESSION:{}:{}", payload.username, payload.thread_id);
    let job_id = format!("{}:{}", session_id, uuid::Uuid::new_v4());

    tracing::info!(
        "Validated & Enqueued:
        \nusername : {username}
        \nsession  : {session_id}
        \nJob ID   : {job_id}
        \nQuery    : {query}",
        username = payload.username,
        session_id = session_id,
        job_id = job_id,
        query = payload.query
    );

    match warden.redis_pool.get().await {
        Ok(mut conn) => {
            let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default();
            let enqueue_time_ms = now.as_millis() as u64;
            let score = enqueue_time_ms as f64;

            let job_data = serde_json::json!({
                "t": 1,
                "f": "Worker.run_task", 
                "a": [
                    payload.query, 
                    payload.options.unwrap_or_default()
                ],
                "k": {},
                "et": enqueue_time_ms
            });

            let pickled = match serde_pickle::to_vec(&job_data, serde_pickle::ser::SerOptions::new()) {
                Ok(data) => data,
                Err(e) => {
                    tracing::error!("RELAY: Serialization error: {}", e);
                    return (StatusCode::INTERNAL_SERVER_ERROR, "Internal serialization failure").into_response();
                }
            };

            let job_key = format!("arq:job:{}", job_id);
            if let Err(e) = conn.set_ex::<_, _, ()>(&job_key, pickled, 86400).await {
                tracing::error!("RELAY: Failed to set job data (aborting enqueue): {}", e);
                warden.breaker.on_error();
                return (StatusCode::INTERNAL_SERVER_ERROR, "Failed to persist job payload").into_response();
            }

            let result: Result<(), _> = conn.zadd("arq:queue", &job_id, score).await;
            match result {
                Ok(()) => {
                    warden.breaker.on_success();
                    (StatusCode::OK, Json(serde_json::json!({"status":"queued","id": job_id}))).into_response()
                },
                Err(e) => {
                    tracing::error!("RELAY: Failed to push to Redis queue: {}", e);
                    warden.breaker.on_error();
                    (StatusCode::INTERNAL_SERVER_ERROR,"Failed to push to queue").into_response()
                }
            }
        },
        Err(e) => {
            tracing::error!("RELAY: Redis Connection Pooling Failed: {}", e);
            warden.breaker.on_error();
            (StatusCode::SERVICE_UNAVAILABLE,"Redis Connection Pool Exhausted").into_response()
        }
    }
}

async fn handle_get_result(
    State(warden): State<Arc<Warden>>,
    Path(job_id): Path<String>,
    axum::extract::Query(params): axum::extract::Query<ResultParams>,
) -> impl IntoResponse {
    // 🛡️ IDOR Check: Prefix validation
    let expected_prefix = format!("SB-SESSION:{}:", params.username);
    if !job_id.starts_with(&expected_prefix) {
        tracing::error!("IDOR Attempt: User {} requested job_id {}", params.username, job_id);
        return (StatusCode::FORBIDDEN, "Access to result denied").into_response();
    }

    let result_key = format!("sb:result:{}", job_id);

    match warden.redis_pool.get().await {
        Ok(mut conn) => {
            let result: Option<String> = conn.get(&result_key).await.unwrap_or(None);

            match result {
                Some(data) => {
                    (StatusCode::OK, Json(serde_json::json!({"status": "complete", "result": data}))).into_response()
                },
                None => {
                    (StatusCode::ACCEPTED, Json(serde_json::json!({"status": "pending"}))).into_response()
                }
            }
        },
        Err(e) => {
            tracing::error!("RELAY: Redis pooling failed on result fetch: {}", e);
            warden.breaker.on_error();
            (StatusCode::SERVICE_UNAVAILABLE, "Redis Connection Pool Exhausted").into_response()
        }
    }
}

async fn handle_health(
    State(warden): State<Arc<Warden>>,
) -> impl IntoResponse {
    match warden.redis_pool.get().await {
        Ok(_) => (StatusCode::OK, Json(serde_json::json!({
            "status": "healthy",
            "circuit_breaker": if warden.breaker.is_call_permitted() { "closed" } else { "open" }
        }))).into_response(),
        Err(_) => (StatusCode::SERVICE_UNAVAILABLE, Json(serde_json::json!({
            "status": "unhealthy",
            "error": "Redis Connection Pool Exhausted"
        }))).into_response()
    }
}