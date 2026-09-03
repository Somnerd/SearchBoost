use crate::Warden;
use axum::{
    extract::{Path, State},
    http::StatusCode,
    response::IntoResponse,
    routing::{get, post},
    Json, Router,
};
use deadpool_redis::redis::AsyncCommands;
use serde::Deserialize;
use std::collections::HashMap;
use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};
use tower_governor::{governor::GovernorConfigBuilder, GovernorLayer};

#[derive(Deserialize, Debug, PartialEq)]
pub struct SearchRequest {
    pub query: String,
    pub thread_id: String,
    pub username: String,
    pub options: Option<HashMap<String, serde_json::Value>>,
}

#[derive(Deserialize, Debug, PartialEq)]
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
        .layer(GovernorLayer {
            config: governor_conf,
        })
        .with_state(warden);

    let addr = format!("{ip}:{port}", ip = "0.0.0.0", port = port);
    let listener = tokio::net::TcpListener::bind(&addr)
        .await
        .expect("FATAL: Cannot bind to relay port");
    tracing::info!(
        "Relay Module listening on {address} [IDOR Protected]",
        address = addr
    );
    axum::serve(
        listener,
        app.into_make_service_with_connect_info::<std::net::SocketAddr>(),
    )
    .await
    .expect("FATAL: Relay server crashed");
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
        Ok(true) => {} // Validated
        Ok(false) => {
            tracing::warn!(
                "Blocked IDOR Attempt: {} tried to access thread {}",
                payload.username,
                payload.thread_id
            );
            return (StatusCode::FORBIDDEN, "Thread access denied").into_response();
        }
        Err(e) => {
            tracing::error!("Database query failed during IDOR check: {}", e);
            warden.breaker.on_error();
            return (
                StatusCode::SERVICE_UNAVAILABLE,
                "Authorization layer unavailable",
            )
                .into_response();
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
            let now = SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap_or_default();
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

            let pickled =
                match serde_pickle::to_vec(&job_data, serde_pickle::ser::SerOptions::new()) {
                    Ok(data) => data,
                    Err(e) => {
                        tracing::error!("RELAY: Serialization error: {}", e);
                        return (
                            StatusCode::INTERNAL_SERVER_ERROR,
                            "Internal serialization failure",
                        )
                            .into_response();
                    }
                };

            let job_key = format!("arq:job:{}", job_id);
            if let Err(e) = conn.set_ex::<_, _, ()>(&job_key, pickled, 86400).await {
                tracing::error!("RELAY: Failed to set job data (aborting enqueue): {}", e);
                warden.breaker.on_error();
                return (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    "Failed to persist job payload",
                )
                    .into_response();
            }

            let result: Result<(), _> = conn.zadd("arq:queue", &job_id, score).await;
            match result {
                Ok(()) => {
                    warden.breaker.on_success();
                    (
                        StatusCode::OK,
                        Json(serde_json::json!({"status":"queued","id": job_id})),
                    )
                        .into_response()
                }
                Err(e) => {
                    tracing::error!("RELAY: Failed to push to Redis queue: {}", e);
                    warden.breaker.on_error();
                    (StatusCode::INTERNAL_SERVER_ERROR, "Failed to push to queue").into_response()
                }
            }
        }
        Err(e) => {
            tracing::error!("RELAY: Redis Connection Pooling Failed: {}", e);
            warden.breaker.on_error();
            (
                StatusCode::SERVICE_UNAVAILABLE,
                "Redis Connection Pool Exhausted",
            )
                .into_response()
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
        tracing::error!(
            "IDOR Attempt: User {} requested job_id {}",
            params.username,
            job_id
        );
        return (StatusCode::FORBIDDEN, "Access to result denied").into_response();
    }

    let result_key = format!("sb:result:{}", job_id);

    match warden.redis_pool.get().await {
        Ok(mut conn) => {
            let result: Option<String> = conn.get(&result_key).await.unwrap_or(None);

            match result {
                Some(data) => (
                    StatusCode::OK,
                    Json(serde_json::json!({"status": "complete", "result": data})),
                )
                    .into_response(),
                None => (
                    StatusCode::ACCEPTED,
                    Json(serde_json::json!({"status": "pending"})),
                )
                    .into_response(),
            }
        }
        Err(e) => {
            tracing::error!("RELAY: Redis pooling failed on result fetch: {}", e);
            warden.breaker.on_error();
            (
                StatusCode::SERVICE_UNAVAILABLE,
                "Redis Connection Pool Exhausted",
            )
                .into_response()
        }
    }
}

async fn handle_health(State(warden): State<Arc<Warden>>) -> impl IntoResponse {
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_search_request_deserialization_full() {
        let json_data = r#"{
            "query": "Rust systems and reliability engineering",
            "thread_id": "thread-uuid-12345",
            "username": "nikolas_alex",
            "options": {
                "max_results": 10,
                "safe_search": true,
                "rerank": "cross-encoder",
                "categories": ["tech", "science"]
            }
        }"#;

        let request: SearchRequest = serde_json::from_str(json_data)
            .expect("SearchRequest should deserialize successfully with all fields");

        assert_eq!(request.query, "Rust systems and reliability engineering");
        assert_eq!(request.thread_id, "thread-uuid-12345");
        assert_eq!(request.username, "nikolas_alex");

        let options = request.options.expect("Options map should be present");
        assert_eq!(
            options.get("max_results").and_then(|v| v.as_u64()),
            Some(10)
        );
        assert_eq!(
            options.get("safe_search").and_then(|v| v.as_bool()),
            Some(true)
        );
        assert_eq!(
            options.get("rerank").and_then(|v| v.as_str()),
            Some("cross-encoder")
        );
        let categories = options
            .get("categories")
            .and_then(|v| v.as_array())
            .unwrap();
        assert_eq!(categories.len(), 2);
        assert_eq!(categories[0], "tech");
        assert_eq!(categories[1], "science");
    }

    #[test]
    fn test_search_request_deserialization_without_options() {
        let json_data = r#"{
            "query": "distributed systems consensus",
            "thread_id": "thread-67890",
            "username": "reliability_eng"
        }"#;

        let request: SearchRequest = serde_json::from_str(json_data)
            .expect("SearchRequest should deserialize successfully without options");

        assert_eq!(request.query, "distributed systems consensus");
        assert_eq!(request.thread_id, "thread-67890");
        assert_eq!(request.username, "reliability_eng");
        assert!(
            request.options.is_none(),
            "Options should be None when omitted"
        );
    }

    #[test]
    fn test_search_request_deserialization_with_null_options() {
        let json_data = r#"{
            "query": "failsafe circuit breaker",
            "thread_id": "thread-null-opt",
            "username": "warden_user",
            "options": null
        }"#;

        let request: SearchRequest = serde_json::from_str(json_data)
            .expect("SearchRequest should deserialize successfully with null options");

        assert_eq!(request.query, "failsafe circuit breaker");
        assert_eq!(request.thread_id, "thread-null-opt");
        assert_eq!(request.username, "warden_user");
        assert!(
            request.options.is_none(),
            "Options should be None when null"
        );
    }

    #[test]
    fn test_search_request_deserialization_with_empty_options() {
        let json_data = r#"{
            "query": "empty options check",
            "thread_id": "thread-empty-opt",
            "username": "tester",
            "options": {}
        }"#;

        let request: SearchRequest = serde_json::from_str(json_data)
            .expect("SearchRequest should deserialize successfully with empty options");

        assert_eq!(request.query, "empty options check");
        let options = request.options.expect("Options should be Some");
        assert!(options.is_empty(), "Options map should be empty");
    }

    #[test]
    fn test_search_request_missing_required_fields() {
        // Missing query
        let missing_query = r#"{"thread_id":"t1","username":"u1"}"#;
        assert!(serde_json::from_str::<SearchRequest>(missing_query).is_err());

        // Missing thread_id
        let missing_thread = r#"{"query":"q1","username":"u1"}"#;
        assert!(serde_json::from_str::<SearchRequest>(missing_thread).is_err());

        // Missing username
        let missing_username = r#"{"query":"q1","thread_id":"t1"}"#;
        assert!(serde_json::from_str::<SearchRequest>(missing_username).is_err());
    }

    #[test]
    fn test_search_request_invalid_field_types() {
        // query is number instead of string
        let invalid_query = r#"{"query": 12345, "thread_id": "t1", "username": "u1"}"#;
        assert!(serde_json::from_str::<SearchRequest>(invalid_query).is_err());

        // thread_id is array instead of string
        let invalid_thread = r#"{"query": "q1", "thread_id": ["t1"], "username": "u1"}"#;
        assert!(serde_json::from_str::<SearchRequest>(invalid_thread).is_err());

        // options is string instead of map/object
        let invalid_options =
            r#"{"query": "q1", "thread_id": "t1", "username": "u1", "options": "invalid"}"#;
        assert!(serde_json::from_str::<SearchRequest>(invalid_options).is_err());
    }

    #[test]
    fn test_result_params_deserialization() {
        let json_data = r#"{"username": "auditor"}"#;
        let params: ResultParams =
            serde_json::from_str(json_data).expect("ResultParams should deserialize");
        assert_eq!(params.username, "auditor");

        let missing = r#"{}"#;
        assert!(serde_json::from_str::<ResultParams>(missing).is_err());
    }

    #[test]
    fn test_idor_prefix_logic() {
        let username = "alice";
        let expected_prefix = format!("SB-SESSION:{}:", username);

        let valid_job_id = "SB-SESSION:alice:550e8400-e29b-41d4-a716-446655440000";
        let attacker_job_id = "SB-SESSION:bob:550e8400-e29b-41d4-a716-446655440000";
        let malformed_job_id = "random-unprefixed-id";

        assert!(valid_job_id.starts_with(&expected_prefix));
        assert!(!attacker_job_id.starts_with(&expected_prefix));
        assert!(!malformed_job_id.starts_with(&expected_prefix));
    }
}
