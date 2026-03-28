# SearchBoost: AI-Powered Semantic Search & Reliability Engine 🛡️🚀

**A distributed 4-tier search architecture featuring a Rust-based reliability sidecar, LLM-driven semantic caching, and a modern React dashboard.**

SearchBoost decouples high-level search logic from low-level infrastructure concerns using the **Warden Authority Sidecar Pattern**. It is designed to be "NetCafe-proof"—resilient to database failures, connection drops, and high concurrency.

---

## 🏗️ System Architecture

### Key Components:
*   **Web Dashboard (React):** Contemporary interactive interface for concurrent thread management.
*   **Edge API (Node.js):** JWT-secured gateway enforcing user ownership and session isolation.
*   **The Warden (Rust Sidecar):** The system's "Source of Truth." It handles GCRA rate limiting and circuit breaking.
*   **The Worker (Python):** Asynchronous task processor for LLM research and Web aggregation.
*   **Infrastructure (Redis/Postgres/SearXNG):** Authenticated backend for caching, state, and meta-search.

---

## 🛡️ Reliability Features

*   **Colon-Delimited Identity**: Delimiter-safe session identifiers to prevent prefix collision attacks.
*   **Circuit Breaking**: Automatically trips when downstream microservices fail.
*   **Fail-Closed Security**: Services crash on boot if required secrets (JWT/DB) are missing.
*   **Unprivileged Containers**: All services run as non-root users.

---

## 🛠️ Project Structure

SearchBoost/
├── configs/              # Unified YAML configurations (master, warden, worker)
├── notes/                # Tech specs and Roadmap
├── scripts/              # Dev utilities (install.sh, log collectors)
├── searchboost_api/      # Express Gateway (Node.js)
├── searchboost_service/  # Research Worker (Python)
├── searchboost_ui/       # Modern Web Interface (React)
└── searchboost_warden/   # Reliability Sidecar (Rust)

---

## 🚀 Getting Started

1.  **Initialize the Environment:**
    ```bash
    ./scripts/install.sh
    ```
2.  **Spin up the Infrastructure:**
    ```bash
    docker-compose up -d --build
    ```
3.  **Access the Dashboard:**
    Open `http://localhost:8080` in your browser.
4.  **Collect Logs for Audit:**
    ```bash
    ./scripts/collect_logs.sh
    ```

---

## �� Technical Roadmap

- [x] **Warden Authority**: Rust-side Job ID generation and enqueuing.
- [x] **Infrastructure Decoupling**: Pure HTTP communication between tiers.
- [x] **Web UI Integration**: React frontend with per-thread history.
- [x] **Security Hardening**: Non-root isolation and authenticated Redis.
- [ ] **Vector Search**: pgvector migration for semantic history retrieval.

---

### 💡 Licensing & Commercial
Licensed under **AGPLv3**. For commercial licensing or proprietary integration, contact: `nikolasalexandrakis.work@gmail.com`.
