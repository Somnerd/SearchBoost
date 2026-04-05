# 🎯 SearchBoost: Master Engineering Roadmap (2026)

This master roadmap consolidates all architecture phases, stabilizing tasks, and the newest feature mandates into a single path forward. 

---

## 🟢 CURRENT STATUS: Phase 6 Fully Hardened

We have successfully completed the **Security & Stability Sweep (Phase 6)**, resolving 11+ critical issues identified by CodeRabbit.

### ✅ RECENT ACHIEVEMENTS (Phase 6)

*   **Critical IDOR Protection**: Implemented colon-delimited session IDs (`SB-SESSION:user:thread`) and strict ownership validation to prevent cross-user data leaks.
*   **Fail-Closed Secrets**: Removed all hardcoded fallback credentials. System now mandates explicit `.env` for boot.
*   **Rootless Containers**: API and UI containers migrated to non-root users (`node`/`nginx-unprivileged`).
*   **Config Precedence**: Fixed Python configurator to prioritize `CLI > ENV > YAML` and implemented recursive deep-merging.
*   **History Synchronization**: Fixed race conditions and logic bypasses in `SearchBoostService.run()` to ensure 100% conversation persistence.
*   **PII-Safe Caching**: Integrated `PIIDetector` with a triple-gate cache strategy.

---

## 🏗️ NEXT OBJECTIVES: Phase 7 & Multi-Tenancy

*   **[ ] Multi-Tenancy isolation**: Deep-test the new colon-separated session IDs with concurrent users in a production-like staging environment.
*   **[ ] Deployment Strategy**: Prepare `docker-compose.prod.yml` with proper ACME/SSL termination and Nginx proxying.
*   **[ ] Vector RAG Integration**: Plan `pgvector` migration for the PostgreSQL database to enable semantic history search.

## 🐛 BUGS & DEBT (KINDLING)

*   [ ] **Entropy/TTL for Time-Sensitive Queries**: Implement context-aware validation or shorter TTLs for caching time-sensitive answers (e.g., current time/date).
*   [ ] **Warden Observation Timestamps**: Fix `sb_warden` observation logic to ensure container logs are captured with accurate timestamps.
*   [ ] **Exponential Backoff**: Replace static polling with jittered backoff logic in the React UI for result fetching.

## 🩹 MAINTENANCE & BUG FIXES (ARCHIVED)

*   [X] **RFC Compliance (SearXNG)**: Renamed `sb_searxng` to `sb-searxng`.
*   [X] **Governor Implementation**: 25 req/s rate limiting with burstfallback of 100 via `tower-governor`.
*   [X] **Web UI & Containerization**: Full React + Node.js + PostgreSQL stack containerized.
*   [X] **(UI) Session Isolation**: Resolved session leakage through multi-thread sidebar implementation.

---

## 🔮 POST-MVP: Intelligence Additions

*   [ ] **Postgres Search**: Implement full-text search and `pgvector` indexing on the local DB.
*   [ ] **SearxNG Local Plugin**: Custom plugin to index and search local project files.
*   [ ] **Normalized IO Handshake**: Define a strictly versioned schema (JSON/Protobuf) for Warden ↔ Service comms.
