# 🎯 SearchBoost: Master Engineering Roadmap (2026)

This master roadmap consolidates all architecture phases, stabilizing tasks, and the newest feature mandates (UI and Governor) into a single path forward.

---

## 🔴 HIGH PRIORITY: Current Objectives (Phase 2 & UI)

* [ ] **Governor Implementation**: Add the `governor` and `tower-governor` crates to the Rust Warden to implement strict GCRA rate limiting on the `/enqueue` endpoint, protecting the downstream AI services.
* [ ] **Web UI & Containerization**: Build a modern, stunning frontend dashboard (e.g. Next.js/Vite) to interact with the Warden's relay API. Write a `Dockerfile` for it and add it to the stack.

## 🐛 BUGS & OVERSIGHTS (KNOWN)
* [ ] **Cache Post-Optimization**: Perform semantic cache checks *after* query optimization, as different inputs may lead to the same optimized search string.
* [ ] **Entropy/TTL for Time-Sensitive Queries**: Implement context-aware validation or shorter TTLs for caching time-sensitive answers (e.g., current time/date).
* [ ] **Warden Observation Timestamps**: Fix `sb_warden` observation logic to ensure container logs are captured with accurate timestamps.
* [ ] **(UI) Session Isolation**: Resolve the bug where chat history includes all previous user messages instead of creating isolated user sessions.

## 🟠 MEDIUM PRIORITY: Build & Environment Stability

*The 10-minute build cycle is currently the primary blocker for feature velocity.*

* [ ] **Docker Cache Optimization**: Refactor `searchboost_warden/Dockerfile` to cache dependencies separately from source (Target: < 2m rebuilds) and implement incremental build volumes (`target/`).
* [ ] **Dev-Mode Toggle**: Update `docker-compose.yml` to support standard `cargo build` (Debug) instead of `--release` for faster local cycles.
* [ ] **Configurator Generalization**:
  * [ ] **Unified Settings**: Move to a master `settings.yaml` shared across Rust and Python.
  * [ ] **Pathing Fix**: Implement absolute pathing in `configurator.py` and Warden to ensure settings are picked up regardless of container working directory.

---

## ✅ Phase 1 & 2: Infrastructure & Abstraction (COMPLETED)
* [X] Fix Network Bindings, Correct Redis Authentication, Visibility Fix, Log Observation.
* [X] Warden Result Polling, Orchestrator Redis Purge, Warden ID Authority.
* [X] Health Check Endpoints (`/health`).
* [X] **Warden Serialization Fix**: Modified Rust relay to produce perfect Tuple pickle bytes to match Arq's default deserializer. (Completed Phase 1 Fixes).

## 🩹 MAINTENANCE & BUG FIXES (RECENT)
* [X] **RFC Compliance (SearXNG)**: Renamed `sb_searxng` to `sb-searxng` to address 400 Bad Request errors caused by underscores in Host headers with the Granian server.
* [X] **Model Updates**: Pulled and configured `llama3.2` image in the `sb_ollama` container for current research tasks.

---

## 🏗️ Phase 3: Resilience & Production Hardening

* [ ] **Exponential Backoff**: Replace static polling with jittered backoff logic in `main.py`.
* [ ] **Request Validation**: Implement strict Pydantic/Rust schema validation for payloads.
* [ ] **Worker Scaling**: Test horizontal scaling of workers with the new Composite Key locality.
* [ ] **Log Rotation**: Ensure `collect_logs.sh` handles log purging and archive management.
* [ ] **Sovereign Handshake**: Finalize the logic where Warden has 100% authority over ID generation and enqueuing.
* [ ] **Health & Observation**:
  * [ ] Integrate **Grafana & Prometheus** for real-time circuit breaker and latency monitoring.

---

## 🚀 Phase 4: Strategy & Architecture Finalization

* [ ] **Folder Separation**: Physical split into `searchboost_client/` and `searchboost_worker/`.
* [ ] **Refine "Self-Hosted" Config**: Ensure the INI/JSON system remains "Enthusiast-Friendly" while supporting enterprise features.
* [ ] **Documentation**: Complete the `SystemDesign.md` and `README.md` reflecting the new "Authority" model.
* [ ] **Test Suite Foundation**:
  * [ ] Create Redis mock for Warden unit tests.
  * [ ] Build a "Sovereign Handshake" integration test script.
  * [ ] Payload injection tests for the Worker.

---

## 🔮 Phase 5: IO Normalization & Generalization (Post-MVP)

*Goal: Replace pickle-based serialization with a standardized, language-agnostic format across the entire service module.*

* [ ] **Normalized IO Handshake**: Define a strictly versioned schema (JSON/Protobuf) for Warden ↔ Service comms.
* [ ] **Translation Adapter**: Implement an adapter in front of the Worker to map standard IO to `arq` inputs.
* [ ] **User Auth Microservice**: Build standalone Auth service & implement JWT propagation from UI → Warden → Worker for multi-tenant isolation.
* [ ] **Update Warden Relay**: Remove pickle dependency and use normalized format.

---

## 🟢 FEATURE ROADMAP: Intelligence Additions
* [ ] **Semantic Caching**: Optimize Ollama for semantic similarity checks to skip redundant web searches.
* [ ] **Postgres Search**: Implement full-text search and `pgvector` indexing on the local DB.
* [ ] **SearxNG Local Plugin**: Custom plugin to index and search local project files.
