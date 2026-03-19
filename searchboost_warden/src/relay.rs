/*
 * SearchBoost: AI-Powered Semantic Search & Reliability Engine
 * Copyright (C) 2026 Nikolaos Alexandrakis
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program. If not, see <https://www.gnu.org/licenses/>.
 *
 * ---------------------------------------------------------------------
 * PROPRIETARY / COMMERCIAL LICENSING:
 * Use of this software in closed-source commercial applications or
 * proprietary stacks is NOT permitted under AGPLv3. For a commercial
 * license, please contact: nikolasalexandrakis.work@gmail.com
 * ---------------------------------------------------------------------
 */


use axum::{routing::{get, post}, Json, Router, extract::{State, Path}, response::IntoResponse, http::StatusCode};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use redis::AsyncCommands;
use std::collections::HashMap;
//use ax_extract = axum::extract::State;
use crate::Warden;
use std::time::{SystemTime, UNIX_EPOCH};



#[derive(Deserialize)]
pub struct SearchRequest {
    pub query: String,
    pub session_id: String,
    pub options: Option<HashMap<String, serde_json::Value>>,
}

struct AppState {
    redis_client: redis::Client,
}

pub async fn start_relay(port: u16, warden: Arc<Warden>) {
    let app = Router::new()
        .route("/health", get(handle_health))
        .route("/enqueue", post(handle_enqueue))
        .route("/results/:job_id", get(handle_get_result))
        .with_state(warden);

    let addr = format!("{ip}:{port}", ip="0.0.0.0", port=port);
    let listener = tokio::net::TcpListener::bind(&addr).await.unwrap();
    tracing::info!("Relay Module listening on {address}", address=addr);
    axum::serve(listener, app).await.unwrap();
}

async fn handle_enqueue(
    State(warden): State<Arc<Warden>>,
    Json(payload): Json<SearchRequest>,
) -> impl IntoResponse {

    if !warden.breaker.is_call_permitted() {
            return (StatusCode::SERVICE_UNAVAILABLE, "Circuit Breaker is OPEN").into_response();
        }

    let job_id = format!("{}:{}", payload.session_id, uuid::Uuid::new_v4());

    tracing::info!(
        "Relaying query for:
        \nsession : {session_id}
        \nJob ID : {job_id}
        \nQuery : {query}",
        session_id = payload.session_id,
        job_id = job_id,
        query = payload.query
        );


    //let mut conn = warden.redis_client.get_async_connection().await.unwrap();

    match warden.redis_client.get_async_connection().await {
        Ok(mut conn) => {

            let now = SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap();

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

            // Serialize as pickle bytes to match Arq's default deserializer (pickle.loads)
            let pickled = serde_pickle::to_vec(&job_data, serde_pickle::ser::SerOptions::new())
                .expect("RELAY: Failed to serialize job data as pickle");

            // Arq Pattern: Store pickled data in arq:job:ID and push ID to arq:queue
            let job_key = format!("arq:job:{}", job_id);
            let _: () = conn.set_ex(&job_key, pickled, 86400).await.unwrap_or_else(|e| {
                tracing::error!("RELAY: Failed to set job data: {}", e);
            });

            let result: Result<(), _> = conn.zadd("arq:queue", &job_id, score).await;

            match result {
                Ok(()) => {
                    warden.breaker.on_success();
                    (StatusCode::OK, Json(serde_json::json!({"status":"queued","id": job_id}))).into_response()
                },
                Err(e) => {
                    tracing::error!("RELAY: Failed to push to Redis queue: {}", e);
                    warden.breaker.on_error();
                    (StatusCode::INTERNAL_SERVER_ERROR,"Failed to push to queue :'( ").into_response()
                }
            }
        },
        Err(e) => {
            tracing::error!("RELAY: Redis Connection Failed: {}", e);
            warden.breaker.on_error();
            (StatusCode::SERVICE_UNAVAILABLE,"Redis Connection Failed :'(").into_response()
        }
    }
}

async fn handle_get_result(
    State(warden): State<Arc<Warden>>,
    Path(job_id): Path<String>,
) -> impl IntoResponse {
    let result_key = format!("arq:result:{}", job_id);

    match warden.redis_client.get_async_connection().await {
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
        Err(_) => {
            warden.breaker.on_error();
            (StatusCode::SERVICE_UNAVAILABLE, "Redis Connection Failed").into_response()
        }
    }
}

async fn handle_health(
    State(warden): State<Arc<Warden>>,
) -> impl IntoResponse {
    match warden.redis_client.get_async_connection().await {
        Ok(_) => (StatusCode::OK, Json(serde_json::json!({
            "status": "healthy",
            "circuit_breaker": if warden.breaker.is_call_permitted() { "closed" } else { "open" }
        }))).into_response(),
        Err(_) => (StatusCode::SERVICE_UNAVAILABLE, Json(serde_json::json!({
            "status": "unhealthy",
            "error": "Redis Connection Failed"
        }))).into_response()
    }
}