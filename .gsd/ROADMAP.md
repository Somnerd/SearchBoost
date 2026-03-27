# SearchBoost Roadmap

## Phase 1: Fix Worker Hangs
**Status**: ✅ Complete
**Branch**: merged → dev
**Summary**: Resolved worker hang root causes. Warden 500 error fixed, job ID double-prefix fixed, Ollama timeout raised to 180s, multi-turn chat persistence via PostgreSQL HistoryService, PII-safe semantic cache (triple-layer gate), rate limiting (tower_governor), client-provided UUIDs, timeout regression tests added.

---

## Phase 2: Web UI
**Status**: ✅ Complete
**Branch**: dev-web-ui
**Plans**:
- ✅ 2.1 Node.js API Scaffold + User Database Schema    [Wave 1]
- ✅ 2.2 Auth Endpoints + JWT Middleware                 [Wave 1]
- ✅ 2.3 Search Proxy + Admin API Routes                 [Wave 2]
- ✅ 2.4 React App Scaffold + Auth Context + Layout      [Wave 2]
- ✅ 2.5 Login + Register Pages                          [Wave 3]
- ✅ 2.6 Search Page (Core Product UI)                   [Wave 3]
- ✅ 2.7 Admin Panel                                     [Wave 4]
- ✅ 2.8 Docker Integration                              [Wave 5]
- ✅ 2.9 Web Stack Stabilization (Poll Resilience)      [Wave 6]
- ✅ 2.10 Chat History Integration                       [Wave 7]

---

## Phase 3: Bug Fixes (Cache & Context Issues)
**Status**: ✅ Complete
**Objective**: Fix the newly discovered bugs from Phase 2 (Cache post-optimization, TTL entropy, container log timestamps, UI session leakage).
**Depends on**: Phase 2

**Tasks**:
- [ ] TBD (run /plan 3 to create)

**Verification**:
- TBD

---

## Phase 4: Environment Stability & Config Generalization
**Status**: ✅ Complete
**Objective**: Overhaul the 25-minute Warden compilation cycle by implementing Rust multi-stage caching and dev-mode toggles, while consolidating environment structures into a single YAML configuration.
**Depends on**: Phase 3

**Tasks**:
- [ ] TBD (run /plan 4 to create)

**Verification**:
- TBD

---

## Phase 5: Concurrent Chat Sessions
**Status**: ✅ Complete
**Objective**: Overhaul the UI and backend history tracking to separate queries into distinct chat threads with a visual sidebar for historical navigation.
**Depends on**: Phase 4

**Tasks**:
- [ ] TBD (run /plan 5 to create)

**Verification**:
- TBD
