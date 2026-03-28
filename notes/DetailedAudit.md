# 🔍 SearchBoost: Detailed Codebase Audit (March 2026)

This document serves as the master technical reference for the SearchBoost architecture, mapping its evolution into a secure, distributed Web-scale system.

---

## 🗺️ 1. System Topology

SearchBoost is a decentralized 4-tier system prioritizing security, high-availability, and LLM research reliability.

| Actor | Language | Role | Key File(s) |
| :--- | :--- | :--- | :--- |
| **Web UI** | React | Modern SPA dashboard with per-thread chat history | `App.jsx`, `Search.jsx` |
| **Edge API** | Node.js | Auth (JWT), Session Mapping, Identity Shield | `auth.js`, `search.js` |
| **Warden** | Rust | GCRA Rate Limiting, Circuit Breaking, ID Authority | `main.rs`, `relay.rs` |
| **Worker** | Python | Semantic Research, Ollama RAG, Persistence | `worker.py`, `service.py` |
| **Infrastructure**| Docker | Redis (Cache), Postgres (State), SearXNG | `docker-compose.yml` |

---

## 🛡️ 2. Edge API (Node.js Gateway)
*Path: `searchboost_api/`*

The Edge API is the primary boundary for user requests. It isolates internal infrastructure from the public internet.
*   **Identity Mapping**: Converts user JWTs into unique **Colon-Delimited Session IDs** (`SB-SESSION:user:thread`).
*   **Security**: Prevents IDOR by validating `job_id` ownership before proxying result fetches to the Warden.
*   **Fail-Closed**: Boots only if `JWT_SECRET` and `DB_PASSWORD` are provided; otherwise, it exits immediately.

---

## 🦀 3. The Warden (Rust Reliability Engine)
*Path: `searchboost_warden/`*

The Warden acts as a high-performance reliability sidecar for the pipeline.
*   **Network Relay**: Provides high-speed ingress for the Node.js API.
*   **Rate Limiting**: Implements `tower_governor` (GCRA) to prevent abusive search spikes (25 req/s).
*   **Circuit Breaker**: Uses the `failsafe` crate to protect the system from Redis or Worker-induced cascaded failures.
*   **Configuration**: Loads from `master_settings.yml` (YAML) with flattened environment overrides (`WARDEN__REDIS__HOST`).

---

## 🏗️ 4. The Worker (Python Research Engine)
*Path: `searchboost_service/`*

The Worker consumes research tasks and executes the search-then-synthesize loop.
*   **Semantic Optimization**: Queries Ollama (`llama3.2`) to refine user intent before searching the web.
*   **Triple-Gate PII Guard**: Uses `PIIDetector` to scan inputs and outputs, ensuring sensitive data is NEVER cached.
*   **Persistence**: Saves every interaction to **PostgreSQL** via `HistoryService` (SQLAlchemy).
*   **Configuration**: Uses Pydantic-Settings for **recursive deep-merging** of YAML and Env vars.

---

## 🔄 5. The Search Lifecycle (Data Flow)

1.  **Ingress**: User submits a query through the React UI.
2.  **Auth**: Node.js API validates JWT and constructs a `SB-SESSION:user:thread` identifier.
3.  **Authority**: Node Calls Warden `POST /enqueue`. Warden generates `SB-SESSION:user:thread:uuid`.
4.  **Enqueue**: Warden pushes the Job ID into Redis (`ZADD arq:queue`).
5.  **Execution**: Python Worker pulls the task from Redis, runs the LLM -> SearXNG -> LLM loop.
6.  **Persistence**: Worker saves turns to Postgres and (if PII-safe) caches response in Redis.
7.  **Polling**: React UI polls Node.js `/api/result/:id`; Node.js verifies ownership and fetches from Warden.

---

## ⚙️ 6. Unified Configuration (YAML Framework)

SearchBoost has migrated from legacy .ini/.json formats to a unified **Master YAML** system:
*   **`configs/master_settings.yml`**: Shared infrastructure defaults (Redis, DB, Search).
*   **`configs/warden.yml`**: Sidecar-specific network and breaker thresholds.
*   **`configs/worker.yml`**: Worker-specific prompt strategies and model parameters.

### Precedence Policy:
`CLI Arguments` > `Environment Variables` > `YAML Overrides` > `Base Defaults`.

---

## 🛠️ Summary of Post-Audit Hardening
*   **Rootless Strategy**: All Docker services run as non-root unprivileged users.
*   **Filesystem Locks**: Sensitive `.env` files are restricted to `chmod 600`.
*   **Delimiter Safety**: Neutralized "alice vs alice2" prefix collision bugs via strict colon delimiters.
*   **Token Isolation**: JWTs delivered via **HttpOnly cookies** only, shielding them from XSS.
