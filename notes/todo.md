
## ✅ Phase 1: Infrastructure & Connection Fixes (COMPLETED)

*Goal: Resolve the "Dizziness" by establishing stable communication.*

* [x] **Fix Network Bindings**: Bound Warden to `0.0.0.0` and Orchestrator to `sb_warden`.
* [x] **Correct Redis Authentication**: Synced `searchboost_pass` across Docker, Python, and Rust.
* [x] **Visibility Fix**: Modernized Rust modules and public structs.
* [x] **Log Observation**: Fixed the "File not found" issue in the Warden's observer with dynamic directory creation.

---

## ✅ Phase 2: The "Senior" Refactor (Warden Abstraction) (COMPLETED)

*Goal: Decouple the client from the database to make it SaaS-ready.*

* [x] **Warden: Implement Result Polling**: Added `/results/{job_id}` endpoint in Rust.
* [x] **Orchestrator: Purge Redis Dependencies**: Happy path is now 100% HTTP-driven.
* [x] **Warden Authority**: Shifted Job ID generation to the Warden using the **Composite Key** pattern (`session:uuid`).
* [x] **Configurator Refactor**: Integrated `WardenSettings` and implemented environment-aware remapping for local testing.

---

## 🏗️ Phase 3: Resilience & Production Hardening

*Goal: Harden the system for public/NetCafe environments.*

* [x] **Health Check Endpoints**: Warden `/health` added.
* [ ] **Warden Serialization Fix**: Make Rust relay produce pickle-compatible bytes to match Arq's default deserializer. (BLOCKER — Worker cannot process Warden-enqueued jobs until this is resolved.)
* [ ] **Build Pipeline Optimization**:
  - [ ] Multi-Stage Dockerfile caching (separate dependency layer from source).
  - [ ] Dev-Mode toggle (Debug builds for local dev, Release for production).
  - [ ] Incremental build volumes (persist `target/` across container restarts).
  - [ ] Fast linker (`mold` or `lld`) inside build stage.
* [ ] **Test Suite Foundation**:
  - [ ] Redis mock for Warden unit tests.
  - [ ] Payload injection tests for the Worker.
  - [ ] Integration "Handshake" test script (Orchestrator → Warden → Redis → Worker).
* [ ] **Exponential Backoff**: Replace static polling with jittered backoff logic in `main.py`.
* [ ] **Request Validation**: Implement strict Pydantic/Rust schema validation for payloads.
* [ ] **Worker Scaling**: Test horizontal scaling of workers with the new Composite Key locality.
* [ ] **Log Rotation**: Ensure the `collect_logs.sh` handles log purging and archive management.

---

## 🚀 Phase 4: Strategy & Architecture Finalization

*Goal: Prepare for Phase 3 Separation (Client vs. Worker).*

* [ ] **Folder Separation**: Physical split into `searchboost_client/` and `searchboost_worker/`.
* [ ] **Refine "Self-Hosted" Config**: Ensure the INI/JSON system remains "Enthusiast-Friendly" while supporting enterprise features.
* [ ] **Documentation**: Complete the `SystemDesign.md` and `README.md` reflecting the new "Authority" model.

---

## 🔮 Phase 5: IO Normalization & Generalization (Post-MVP)

*Goal: Replace pickle-based serialization with a standardized, language-agnostic format across the entire service module.*

* [ ] **Design a unified serializer/deserializer** for cross-language IO (e.g., msgpack or Protocol Buffers).
* [ ] **Update Worker `WorkerSettings`** with custom `job_serializer`/`job_deserializer`.
* [ ] **Update Fallback Handler** to use the same serialization contract.
* [ ] **Update Warden Relay** to use the normalized format (removing pickle dependency).
* [ ] **Regression tests** to verify the Handshake survives the format migration.

*This is deferred until after: Warden MVP ✅ → Test Suites ✅ → UI ✅*

---

### 💡 Current Status

* **Warden**: **The Authority.** Generates IDs, manages circuits, and observes worker health. Healthy and Dockerized.
* **Orchestrator**: **Pure Consumer.** Talks HTTP to Warden, has no Redis dependency on happy path.
* **Worker**: Functional via Fallback path. **Blocked** on Warden path due to serialization mismatch (JSON vs pickle).
* **Infrastructure**: Aggregated logs via `collect_logs.sh`, unified INI configuration in place.
