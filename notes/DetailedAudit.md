# 🔍 SearchBoost: Detailed Codebase Audit (March 2026)

This document serves as a master reference for the SearchBoost architecture. It maps the evolution of the project from a simple search tool into a decentralized, resilient "Warden Authority" system.

---

## 🗺️ 1. System Topology

SearchBoost is divided into three primary "Actors" and a shared "Infrastructure" layer.

| Actor | Language | Role | Key File(s) |
| :--- | :--- | :--- | :--- |
| **Warden** | Rust | Reliability Sidecar, ID Authority, Circuit Breaker | `main.rs`, `relay.rs` |
| **Orchestrator** | Python | Client UI, Query Optimization, Routing | `main.py`, `configurator.py` |
| **Worker** | Python | Fact-finding, LLM Research, Persistence | `worker.py`, `service.py` |
| **Infrastructure** | Docker | Redis (Broker), Postgres (Memory), SearxNG | `docker-compose.yml` (e.g., `sb-searxng`) |

---

## 🛡️ 2. The Warden (Rust Sidecar)
*Path: `searchboost_warden/`*

The Warden is the gatekeeper of the system. It ensures that the Python client doesn't overwhelm the backend and acts as the "Source of Truth" for job identities.

### Key Modules:
*   **`relay.rs`**: The heart of the sidecar. 
    *   **Authority**: It generates the `session:uuid` composite key.
    *   **Enqueuing**: Uses `ZADD` to push jobs into Redis in the format `arq` expects (including Unix timestamps as scores). It natively serializes job payloads into Python's `pickle` binary format using the `serde-pickle` crate for perfect cross-language compatibility.
    *   **Result Proxy**: Provides the `GET /results/:id` endpoint so the client never has to touch Redis directly.
*   **`configurator.rs`**: Uses the `config` crate to merge `warden.ini` and environment variables.
*   **`breaker.rs`**: Implements a **Circuit Breaker**. If Redis fails multiple times, the breaker "Opens," and the Warden returns `503 Service Unavailable` to the client.
*   **`observer.rs`**: Logs into the Docker daemon via `bollard`. It watches the `sb_worker` container and replicates its logs to `./logs/service_observation.log`, alerting on errors.

---

## 🐍 3. The Orchestrator (Python Client)
*Path: `searchboost_service/`*

The Orchestrator is the intelligence layer. It handles the "Human" side of the search.

### Key Modules:
*   **`main.py`**: The entry point. It attempts to talk to the Warden first. If the Warden is down or the circuit is open, it automatically triggers the **Fallback**.
*   **`configurator.py`**: A complex, environment-aware settings manager built on Pydantic. 
    *   **Hierarchy**: CLI Args > Environment Vars (`SEARCHBOOST_`) > JSON Files > Defaults.
    *   **Local Routing**: If you run on your host machine (not in Docker), it automatically maps `sb_redis` to `127.0.0.1`.
*   **`fallback_handler.py`**: The "Safe Mode." It contains the logic to talk directly to Redis/Arq using the `arq` library, bypassing the Warden sidecar entirely if necessary.

---

## 🏗️ 4. The Worker (Python Processor)
*Path: `searchboost_service/searchboost_src/`*

The Worker is where the heavy lifting happens. It is triggered by the Warden's Redis push.

### Key Modules:
*   **`worker.py`**: The Arq worker implementation. It listens for the `run_task` function call.
*   **`service.py`**: Contains the `SearchBoostService` class.
    *   **Efficiency**: Check Redis Cache -> Optimize Query via LLM -> Web Search (SearxNG) -> Final LLM Synthesis.
    *   **`PersistenceService`**: A child class that saves the final `SearchResult` into **PostgreSQL** using SQLAlchemy.
*   **`database.py` & `models.py`**: Define the SQLAlchemy models and the Postgres connection pool logic.

---

## 🔄 5. The Search Lifecycle (Data Flow)

1.  **Submission**: User runs `main.py --query "X"`.
2.  **Authority Check**: `main.py` calls Warden `POST /enqueue`.
3.  **Key Generation**: Warden creates `{session}:{uuid}`, calculates a timestamp score, and runs `ZADD arq:queue`.
4.  **Acknowledgment**: Warden returns the ID to the Client. Client enters a polling loop: `GET /results/{id}`.
5.  **Execution**: `sb_worker` sees the new item in Redis. It triggers `Worker.run_task`.
6.  **Research**: Worker queries `Ollama` for a better search string, hits `SearxNG` for data, then `Ollama` again for the final answer.
7.  **Archival**: Worker writes the answer to **Postgres** and caches the result in **Redis**.
8.  **Completion**: Warden sees `arq:result:{id}` in Redis and serves it to the Client loop.

---

## ⚙️ 6. Configuration Management

### Warden (`warden.ini`)
*   **`[network]`**: Controls the sidecar listening port (default: 14141).
*   **`[redis]`**: Credentials for the message broker.
*   **`[breaker]`**: Thresholds for when to trip the circuit (e.g., 5 failures).

### Orchestrator (`configs/*.json`)
*   **`web_search.json`**: Configure SearxNG instance and engine types.
*   **`local_ai.json`**: Configure local Ollama model names and ports.
*   **`service_settings.json`**: High-level strategy overrides.

---

## 🛠️ Summary of "Hidden" Intelligence
*   **Redis Hash Tags**: The use of `{session}:uuid` ensures all data for one user hits the same Redis shard in a cluster environment.
*   **Docker Logic**: The system knows when it is inside a container vs on your Desktop and adjusts its networking automatically.
*   **Multiplexing**: The Warden uses a shared Redis client to avoid TCP connection overhead.
