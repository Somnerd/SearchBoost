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
- [x] 7.3 **pgvector Migration**: Initialize `pgvector` in PostgreSQL for vector storage.
- [x] 7.4 **Semantic Persistence**: Synchronous embedding generation for conversation history.
- [x] 7.5 **History Search API**: New `POST /api/search/history/search` endpoint.
- [x] 7.6 **Context Injection**: Automated cross-session context discovery for research.
- [x] 7.7 **Worker Scaling**: Horizontal scaling with Redis task locality.
- [x] 7.8 **Dynamic LLM Selection**: Allow UI/Terminal overrides for Ollama model names.
- [ ] 7.9 **Performance Benchmarks**: Document latencies under load.
- [ ] 7.10 **Audit Polish**: Resolve remaining minor CodeRabbit suggestions:
    - [ ] Entropy/TTL for time-sensitive queries.
    - [ ] Accurate timestamps for Warden observation logs.
    - [ ] Exponential backoff with jitter in React UI.
    - [ ] Standardized `Result` types in Rust components.

---


## Phase 8: Hybrid Shift & IO Normalization (90-Day Sprint: Month 1)
**Objective**: Standardize the communication "Contract" and migrate performance logic.

**Plans**:
- [ ] 8.1 **gRPC Handshake**: Replace Pickle with Protobuf for Rust ↔ Python ↔ Node safety.
- [ ] 8.2 **Valkey Migration**: Drop-in swap of Redis for Valkey (Linux Foundation fork).
- [ ] 8.3 **Rust Logic Migration**: Port `PIIDetector` and "Fast-Path" (cache) logic into the Warden.
- [ ] 8.4 **Telemetry & Dashboards**: Prometheus/Grafana integration for Warden Circuit Breakers (`failsafe` crate).
- [ ] 8.5 **Direct Inference**: Prepare `llama.cpp` wrapper for the Warden.
- [ ] 8.6 **UI Observability**: Real-time research progress tracking in React dashboard.

---


## Phase 9: Knowledge Ingestion & Serverless RAG (90-Day Sprint: Month 2)
**Objective**: Transition to Zero-Ops infrastructure with deep local intelligence.

**Plans**:
- [ ] 9.1 **Local Ingest Crawler**: Build a Python-based worker to scan and embed local files (PDF/MD/TXT).
- [ ] 9.2 **LanceDB Migration**: Replace `pgvector/PostgreSQL` with embedded `LanceDB` for serverless storage.
- [ ] 9.3 **Firecrawl & Tantivy Integration**: Replace SearXNG with Firecrawl (Web) and Tantivy (Local) for precision search.
- [ ] 9.4 **Hybrid Search Logic**: Update SearchBoost loop to query **LanceDB + Firecrawl + Tantivy** in parallel.
- [ ] 9.5 **Context synthesis**: Prompt LLM to reconcile local "Truth" with Web "News".

---


## Phase 10: Enterprise Connectivity & Data Sovereignty
**Objective**: Support B2B integrations with legacy and external data sources.

**Plans**:
- [ ] 10.1 **External DB Connectors**: Build "Plug-and-Play" connectors for existing enterprise DBs (SQL Server, Oracle, External Postgres).
- [ ] 10.2 **Warden API Keys**: Implement per-client multi-tenancy and quota management in the Rust Warden.
- [ ] 10.3 **OIDC / IAP Auth**: Zero-trust identity management for corporate internal deployment.

## PHAS 11
**Plans**:
- [ ] 11.1 **Local Ingest Crawler**: Build a Python-based worker to scan and embed local files (PDF/MD/TXT) into `pgvector`.
- [ ] 11.2 **Embedding Pipeline**: Integrate Ollama embeddings (e.g. `nomic-embed-text`) for local chunking.
- [ ] 11.3 **Hybrid Search Logic**: Update SearchBoost loop to query **Local Vector Store + SearXNG** in parallel.
- [ ] 11.4 **Context synthesis**: Prompt LLM to reconcile local "Truth" with Web "News".
- [ ] 11.5 **Rust Logic Migration**: Port `PIIDetector` and "Fast-Path" (cache) logic into the Warden.
- [ ] 11.6 **Telemetry & Dashboards**: Prometheus/Grafana integration for Warden Circuit Breakers.
- [ ] 11.7 **UI Observability**: Real-time research progress tracking in React dashboard.