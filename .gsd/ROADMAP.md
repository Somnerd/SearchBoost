# SearchBoost Roadmap


## Phase 1: Fix Worker Hangs
**Status**: ✅ Complete

---


## Phase 2: Web UI
**Status**: ✅ Complete

---


## Phase 3: Bug Fixes (Cache & Context Issues)
**Status**: ✅ Complete

---


## Phase 4: Environment Stability & Config Generalization
**Status**: ✅ Complete

---


## Phase 5: Concurrent Chat Sessions
**Status**: ✅ Complete

---


## Phase 6: CodeRabbit Security & Stability Sweep
**Status**: ✅ Complete
**Summary**: SearchBoost is a decentralized, resilient hybrid-AI search engine pipeline. It is architected as an asynchronous distributed system isolating user authorization (Node.js), performant boundary ingress/caching (Rust), resource-intensive background execution (Python), and frontend client rendering (React). The system is configured for security, enforcing fail-closed configuration and unprivileged container execution.

---


## Phase 7: Production Rigor & Vector Search (In Progress)
**Objective**: Architecture hardening for deployment and semantic discovery.

**Plans**:
- [x] 7.1 **Production Proxy**: Mask raw backend errors and enforce 503 masking.
- [x] 7.2 **Container Health**: Standardize HEALTHCHECK instructions across Dockerfiles.
- [ ] 7.3 **pgvector Migration**: Initialize `pgvector` in PostgreSQL for vector storage.
- [ ] 7.4 **Worker Scaling**: Horizontal scaling with Redis task locality.
- [ ] 7.5 **Dynamic LLM Selection**: Allow UI/Terminal overrides for Ollama model names.
- [ ] 7.6 **Performance Benchmarks**: Document latencies under load.

---


## Phase 8: Hybrid Shift & IO Normalization
**Objective**: Standardize the communication "Contract" and migrate performance-critical paths into Rust.

**Plans**:
- [ ] 8.1 **gRPC Handshake**: Replace Pickle with Protobuf for Rust ↔ Python ↔ Node safety.
- [ ] 8.2 **Rust Logic Migration**: Port `PIIDetector` and "Fast-Path" (cache) logic into the Warden.
- [ ] 8.3 **Telemetry & Dashboards**: Prometheus/Grafana integration for Warden Circuit Breakers.
- [ ] 8.4 **UI Observability**: Real-time research progress tracking in React dashboard.

---


## Phase 9: Knowledge Ingestion & Hybrid RAG (MVP Hook)
**Objective**: Combine local "Expert Knowledge" with "Global Web Research" for unprecedented answer quality.

**Plans**:
- [ ] 9.1 **Local Ingest Crawler**: Build a Python-based worker to scan and embed local files (PDF/MD/TXT) into `pgvector`.
- [ ] 9.2 **Embedding Pipeline**: Integrate Ollama embeddings (e.g. `nomic-embed-text`) for local chunking.
- [ ] 9.3 **Hybrid Search Logic**: Update SearchBoost loop to query **Local Vector Store + SearXNG** in parallel.
- [ ] 9.4 **Context synthesis**: Prompt LLM to reconcile local "Truth" with Web "News".
