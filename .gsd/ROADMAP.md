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
**Branch**: dev-web-ui
**Summary**: Successfully resolved 14 critical security and architectural flaws. Implemented "Secure-by-Default" posture with non-root containers, colon-delimited identity isolation, and fail-closed secret management.

---

## Phase 7: Production Rigor & Vector Search 🏃 Next UP
**Objective**: Transition the "Pristine" dev state into a hardened public-facing deployment while improving search retrieval performance.

**Plans**:
- [ ] 7.1 **Production Reverse Proxy**: Deploy an Nginx container with SSL/TLS (Certbot/ACME) to protect the Edge API.
- [ ] [**pgvector**] **Migration**: Migrate PostgreSQL history to use vector embeddings for semantic similarity search within past threads.
- [ ] **Worker Horizontal Scaling**: Implement and test multi-worker concurrency with synchronized Redis state.
- [ ] **Performance Audit**: Benchmarking system latencies under load (10+ concurrent users).

---

## Phase 8: IO Normalization & Observability
**Objective**: Finalize the system's "Authority" model by removing legacy binary serialization (Pickle) and integrating real-time telemetry.

**Plans**:
- [ ] **JSON/Protobuf Handshake**: Standardize cross-language communication (Rust ↔ Python ↔ Node) to remove the Pickle dependency.
- [ ] **Grafana/Prometheus Dashboard**: Real-time metrics for Warden Circuit-Breaker state and LLM research pipeline latency.
- [ ] **Exponential Backoff**: Jittered polling strategy for the React UI to optimize resource utilization.
