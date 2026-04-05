# SearchBoost Roadmap

## Phase 1 - 5: Foundation & Stabilization
**Status**: ✅ Complete

## Phase 6: CodeRabbit Security & Stability Sweep
**Status**: ✅ Complete

## Phase 7: Production Rigor, Vector Search & Death Audit Resilience
**Status**: ✅ Complete
**Objective**: Architecture hardening, semantic discovery, and addressing structural vulnerabilities from the Death Audit.

**Completed Plans**:
- [x] 7.1 **Production Proxy**: Mask raw backend errors and enforce 503 masking.
- [x] 7.2 **Container Health**: Standardize HEALTHCHECK instructions across Dockerfiles.
- [x] 7.3 **pgvector Migration**: Initialize `pgvector` in PostgreSQL for vector storage.
- [x] 7.4 **Semantic Persistence**: Synchronous embedding generation for conversation history.
- [x] 7.5 **History Search API**: New `POST /api/search/history/search` endpoint.
- [x] 7.6 **Context Injection**: Automated cross-session context discovery for research.
- [x] 7.7 **Worker Scaling**: Horizontal scaling with label-based discovery.
- [x] 7.8 **Dynamic LLM Selection**: UI/Terminal overrides for Ollama model names.
- [x] 7.9 **Performance Benchmarks**: Document latencies under distributed load.
- [x] 7.10 **Death Audit Stabilization**: 
    - [x] API migrated from Vanilla JS to strict TypeScript + Prisma ORM.
    - [x] Rust Warden proxy engineered with `deadpool-redis` & `tokio-retry` exponential backoff.
    - [x] Python God Object decoupled into isolated `CacheService` and `ContextService`.

---

## Phase 8: The Safety Net & Strict Contracts (90-Day Sprint: Month 1)
**Objective**: Establish a bulletproof testing culture and enforce strict communication boundaries to eradicate magic strings across languages.

**Plans**:
- [ ] 8.1 **Test-Driven Operations**: Replace the API scaffold with >80% code coverage integration tests using Jest & Supertest.
- [ ] 8.2 **gRPC / Protobuf Handshake**: Eradicate `SB-SESSION:` string concatenation and `Pickle` vulnerabilities by standardizing on Protobuf between Rust, Python, and Node.
- [ ] 8.3 **Valkey Migration**: Drop-in swap of Redis for Valkey (Linux Foundation fork).
- [ ] 8.4 **Telemetry & Dashboards**: Prometheus/Grafana integration for Warden Circuit Breakers (`failsafe` crate) and API latency metrics.
- [ ] 8.5 **Direct Inference**: Prepare `llama.cpp` wrapper for the Warden.
- [ ] 8.6 **UI Observability**: Real-time research progress tracking in React dashboard.

---

## Phase 9: Knowledge Ingestion & Zero-Ops Architecture (90-Day Sprint: Month 2)
**Objective**: Transition to Zero-Ops infrastructure, dropping bloated PostgreSQL requirements for local setups while maintaining edge execution.

**Plans**:
- [ ] 9.1 **Local Ingest Crawler**: Build a Python-based worker to scan and embed local files (PDF/MD/TXT).
- [ ] 9.2 **LanceDB Migration**: Replace Prisma/Postgres bloat with embedded `LanceDB` for serverless local storage. This eliminates the heavy DB query-engine cold starts identified in the Audit.
- [ ] 9.3 **Firecrawl & Tantivy Integration**: Blend Firecrawl (Web) and Tantivy (Local) for precision semantic search alongside existing providers.
- [ ] 9.4 **Hybrid Search Logic**: Update SearchBoost loop to seamlessly synthesize context from **LanceDB (Local Context) + Firecrawl (Web)** in parallel.
- [ ] 9.5 **Context Reconciliation**: Prompt engineered LLM chains to reconcile conflicting signals between Local "Truth" and Web "News".

---

## Phase 10: Enterprise Connectivity & Data Sovereignty (90-Day Sprint: Month 3)
**Objective**: Expand the pipeline for B2B adaptation, allowing SearchBoost to natively adapt to existing Corporate tech stacks.

**Plans**:
- [ ] 10.1 **Enterprise Connector SDK**: Build "Plug-and-Play" outbound sync for LanceDB to mirror data into legacy enterprise RDBMS (SQL Server, Oracle, Corporate Postgres) for B2B continuity.
- [ ] 10.2 **Warden API Quotas**: Implement per-client multi-tenancy (API Keys) and strict request shaping in the Rust Warden.
- [ ] 10.3 **OIDC / IAP Auth**: Zero-trust identity management integration for Corporate Intranet deployment (PingIdentity, Entra ID).