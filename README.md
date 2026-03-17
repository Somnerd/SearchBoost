# SearchBoost: AI-Powered Semantic Search & Reliability Engine 🛡️🚀

**A distributed search architecture featuring a Rust-based reliability sidecar, LLM-driven semantic caching, and multi-engine aggregation.**

SearchBoost decouples high-level search logic from low-level infrastructure concerns using the **Warden Authority Sidecar Pattern**. It is designed to be "NetCafe-proof"—resilient to database failures, connection drops, and high concurrency.

---

## 🏗️ System Architecture

### Key Components:
*   **The Warden (Rust Sidecar):** The system's "Source of Truth." It generates tracking IDs, manages Redis enqueuing, and handles **Circuit Breaking** to protect the backend.
*   **The Orchestrator (Python):** The intelligence layer. It talks exclusively via HTTP to the Warden on the happy path, handling query optimization and result formatting.
*   **The Worker (Python/Arq):** Asynchronous task processor that handles LLM embeddings and web engine scaling.
*   **Infrastructure (Redis/Postgres/SearxNG):** The distributed storage and search engine backend.
    *   **PostgreSQL Persistence**: Automatic long-term storage of LLM responses and system indexing metadata.

---

## 🛡️ Reliability Features

*   **Composite Key Locality**: Uses `{session}:uuid` formatting to ensure data stays close to the user in clustered environments.
*   **Circuit Breaking**: Automatically trips when Redis or the Worker fails, routing traffic through an isolated **Fallback Handler**.
*   **Log Observation**: The Warden observes Docker container health in real-time.

---

## 🛠️ Project Structure

```bash
<<<<<<< HEAD
SearchBoost/
├── configs/              # Unified INI/JSON configurations
├── logs/                 # Aggregated log directory (Worker, Warden, DB)
├── notes/                # Tech specs and Roadmap
├── scripts/              # Dev utilities (log collectors, permission fixes)
├── searchboost_service/  # Orchestrator & Client logic (Python)
└── searchboost_warden/   # The Reliability Sidecar (Rust)
=======
   git clone https://github.com/Somnerd/SearchBoost.git
```
2. **Build the Infrastructure:**
```Bash
    docker-compose build --no-cache
```

3. **Spin up the Infrastructure:**
```Bash
    docker-compose up -d
```
4.  **Run the Search Pipeline:**
```Bash
    cd searchboost_src && python main.py --query "architecture patterns"
>>>>>>> main
```

---

## 🚀 Getting Started

1.  **Spin up the Infrastructure:**
    ```bash
    docker-compose up -d --build
    ```
2.  **Run a Search (Happy Path):**
    ```bash
    cd searchboost_service && python main.py --query "architecture patterns"
    ```
3.  **Collect Logs for Audit:**
    ```bash
    ./scripts/collect_logs.sh
    ```

---

## 🚦 Technical Roadmap

- [x] **Warden Authority**: Rust-side Job ID generation and enqueuing.
- [x] **Infrastructure Decoupling**: Pure HTTP communication between Client and Sidecar.
- [ ] **Exponential Backoff**: Jittered polling strategy for high-load scaling.
- [ ] **Vector Similarity Logic**: Redis-based semantic caching for LLM responses.

---

### 💡 Licensing & Commercial
Licensed under **AGPLv3**. For commercial licensing or proprietary integration, contact: `nikolasalexandrakis.work@gmail.com`.
