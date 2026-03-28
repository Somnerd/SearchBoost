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
**Summary**: Resolved 14+ architectural vulnerabilities. Implemented non-root isolation and fail-closed secret management.

---

## Phase 7: Production Rigor & Vector Search 🏃 Next UP
**Objective**: Hardening for public deployment and semantic discovery.

**Plans**:
- [ ] 7.1 **Production Proxy**: Deploy Nginx Reverse Proxy with SSL/ACME.
- [ ] 7.2 **pgvector Migration**: Enable semantic history similarity search.
- [ ] 7.3 **Worker Scaling**: Horizontal scaling with Redis task locality.
- [ ] 7.4 **Dynamic LLM Selection**: Allow UI/Terminal overrides for Ollama model names (e.g., `mistral`, `llama3.2`).
- [ ] 7.5 **Performance Benchmarks**: Document latencies under load.

---

## Phase 8: Hybrid Shift & IO Normalization
**Objective**: Standardize the communication "Contract" and migrate performance-critical paths into Rust.

**Plans**:
- [ ] 8.1 **gRPC Handshake**: Replace Pickle with Protobuf for Rust ↔ Python ↔ Node safety.
- [ ] 8.2 **Rust Logic Migration**: Port `PIIDetector` and "Fast-Path" (cache) logic into the Warden.
- [ ] 8.3 **Telemetry & Dashboards**: Prometheus/Grafana integration for Warden Circuit Breakers.
- [ ] 8.4 **UI Observability**: Real-time research progress tracking in React dashboard.
