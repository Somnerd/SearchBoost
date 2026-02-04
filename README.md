# SearchBoost: AI-Powered Semantic Search & Reliability Engine 🛡️🚀

**A distributed search architecture featuring a Rust-based reliability sidecar, LLM-driven semantic caching, and multi-engine aggregation.**

SearchBoost isn't just a search tool; it's a resilience-first infrastructure project designed to handle the complexities of modern AI data pipelines. It decouples high-level search logic from low-level infrastructure concerns using the **Sidecar Pattern**.

---

## 🏗️ System Architecture

The project implements a "Reliability Sidecar" model to manage communication between a Python-based intelligence layer and a diverse backend stack.



### Key Components:
* **The Warden (Rust Sidecar):** A high-performance TCP proxy built with **Tokio**. It handles **Circuit Breaking** (via `failsafe`) to protect the backend from cascading failures.
* **Search Intelligence (Python):** Orchestrates the search lifecycle, integrating **Ollama** for embeddings and **Searxng** for aggregated results.
* **Semantic Cache (Redis):** Stores vector embeddings to provide instant hits for semantically similar queries, reducing LLM API costs and latency.
* **Persistence Layer (PostgreSQL):** Serves as the source of truth for relational data and metadata.

---

## 🛡️ Resilience & Reliability (The Warden)

The Warden monitors the health of the system. If the database or caching layer becomes saturated or unresponsive:
1.  **Detection:** Monitors consecutive connection failures.
2.  **Tripping:** The circuit "opens," immediately rejecting requests to prevent resource exhaustion.
3.  **Recovery:** Automatically enters a "half-open" state to test backend health before resuming full traffic.



---

## 🚀 Technical Roadmap

- [ ] **Dynamic Configuration:** Implement JSON-based service discovery within the Warden for zero-downtime re-routing.
- [ ] **Vector Similarity Logic:** Finalize the Cosine Similarity comparison within the Redis/Ollama semantic cache layer.
- [ ] **Multi-Engine Aggregation:** Complete the Searxng bridge to merge external web results with internal database records.
- [ ] **Chaos Engineering & Testing:**
    - [ ] **Pytest Suite:** E2E testing for the search pipeline.
    - [ ] **Failure Injection:** Automated scripts to drop database containers and verify Warden's circuit-breaking response.
- [ ] **Observability:** Prometheus/Grafana integration to track latency overhead and circuit state transitions.

---

## 🛠️ Stack

| Layer | Technology |
| :--- | :--- |
| **Systems/Proxy** | Rust (Tokio, Failsafe) |
| **Backend Logic** | Python 3.11+, AsyncIO |
| **Search Engine** | RedisSearch, Searxng |
| **Database** | PostgreSQL |
| **Intelligence** | Ollama (LLM Embeddings) |
| **Infrastructure** | Docker, Docker-Compose |

---

## 🚦 Getting Started

1. **Clone the Repo:**
```bash
   git clone https://github.com/Somnerd/SearchBoost.git
```
2. **Spin up the Infrastructure:**
```Bash
    docker-compose up -d
```
3. ***Start the Warden (Rust Sidecar):***
```Bash
    cd searchboost_warden && cargo run
```
4.  **Run the Search Pipeline:**
```Bash
    cd searchboost_src && python main.py --query "architecture patterns"
```
