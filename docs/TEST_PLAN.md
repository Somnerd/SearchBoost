# 🧪 SearchBoost: Master Test Plan & QA Verification Manual

**Document Version:** 1.0.0  
**Project:** SearchBoost (AI Cognitive Search & Vector Grounding Engine)  
**Target Repository:** `Somnerd/SearchBoost`  
**Execution Environment:** Self-Hosted Linux Runner (Ubuntu 22.04 LTS / WSL2)  
**Verification Scope:** All 4 System Tiers (Rust, Node/TS, React, Python)  

---

## 1. Objectives & Scope

This Master Test Plan defines the automated testing criteria, verification strategies, operational matrices, edge cases, and continuous integration procedures for the entire SearchBoost distributed architecture.

### Primary Objectives:
1. **Multi-Mode Execution Integrity:** Verify faultless execution across the 4-mode operational matrix (`deep:web`, `deep:local`, `fast:web`, `fast:local`).
2. **Zero-Leakage Offline Guarantee:** Ensure that when `web_search=false`, zero external network calls are dispatched to SearXNG or public search domains.
3. **Sub-Millisecond Cache Isolation:** Ensure Redis cache keys are segmented strictly by query mode to prevent cross-mode cache poisoning.
4. **Vector Retrieval Precision:** Validate pgvector cosine distance calculations (`<=>`) with 768-dimensional embeddings, similarity thresholds, and idempotent re-indexing.
5. **Multi-Tier Fault Resilience:** Verify system resilience during simulated outages of downstream services (PostgreSQL, Ollama, SearXNG, Redis).
6. **Zero Cloud Cost CI:** Maintain 100% test automation on self-hosted runners without cloud egress or runner billing.

---

## 2. System Under Test (SUT) & Architecture Topology

```
┌────────────────────────────────────────────────────────────────────────┐
│                          TIER 3: REACT 19 UI                           │
│  • Mode Radiogroup (Deep Research vs Fast Answer)                      │
│  • Web Search Switch (Web Search: ON vs OFF)                           │
│  • Real-time Pending State Badges ([🌐 Web Search], [🔌 Local Knowledge])│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST (/api/search/enqueue)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        TIER 2: EXPRESS 5 / TS API                      │
│  • Authentication (JWT & HTTP-only Cookies)                            │
│  • IDOR Session Sharding (SB-SESSION:{user}:{thread}:{uuid})           │
│  • Document Catalog Summary (GET /api/search/docs)                     │
└───────────────────┬───────────────────────────────┬────────────────────┘
                    │                               │ HTTP Proxy
                    ▼                               ▼
    ┌───────────────────────────────┐ ┌──────────────────────────────────┐
    │     POSTGRESQL 16 + PGVECTOR  │ │      TIER 1: RUST WARDEN         │
    │  • users & auth_tokens        │ │  • Failsafe Circuit Breakers     │
    │  • conversation_turns (vec)   │ │  • Governor Rate Limiting        │
    │  • internal_documents (vec)   │ │  • Bollard Docker Observer       │
    └───────────────────────────────┘ └─────────────┬────────────────────┘
                                                    │ ARQ Job Queue
                                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       TIER 4: PYTHON ASYNC WORKER                      │
│  • Query Optimizer (LLM reason="optimization")                         │
│  • Meta-Search Collector (SearXNG HTTP / JSON)                         │
│  • Semantic Context & Memory (DocumentService & HistoryService)        │
│  • Mode-Scoped Response Caching (Redis CacheService)                   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Operational Test Matrices

### 3.1 The 4-Mode Execution Matrix

| Mode | `research_mode` | `web_search` | Query Optimizer | SearXNG Retrieval | Local Vector Retrieval | Redis Cache Tag |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Deep Research (Online)** | `true` | `true` | **Active** | **Active** (top-5 snippets) | **Active** (pgvector docs) | `deep:web` |
| **Deep Research (Offline)** | `true` | `false` | **Active** | **BYPASSED (0 calls)** | **Active** (pgvector docs) | `deep:local` |
| **Fast Answer (Online)** | `false` | `true` | **Bypassed** | **Active** (top-5 snippets) | **Active** (pgvector docs) | `fast:web` |
| **Fast Answer (Offline)** | `false` | `false` | **Bypassed** | **BYPASSED (0 calls)** | **Active** (pgvector docs) | `fast:local` |

---

## 4. Test Suites by Tier

### 4.1 Tier 1: Rust Warden Sidecar (`searchboost_warden`)
- **Location:** `searchboost_warden/`
- **Framework:** Rust `cargo test`, `cargo clippy`, `cargo fmt`
- **Test Count:** 18 Tests
- **Coverage Areas:**
  - `relay`: HTTP endpoints (`/health`, `/enqueue`, `/results/:job_id`)
  - `breaker`: Circuit breaker state transitions (`Closed` -> `Open` -> `Half-Open`)
  - `configurator`: Environment and YAML parser fallbacks
  - `observer`: Docker event parser & container health probes

### 4.2 Tier 2: Node.js / Express 5 API (`searchboost_api`)
- **Location:** `searchboost_api/tests/app.test.ts`
- **Framework:** Jest, Supertest, TypeScript compiler (`tsc --noEmit`)
- **Test Count:** 32 Tests
- **Coverage Areas:**
  - `Health Route`: Database up (200) vs down (503)
  - `Auth Routes`: Register, login, JWT issuance, `/me` validation
  - `Admin & RBAC`: Admin escalation prevention, self-deletion blocks, health probes
  - `Search & Relay`: Enqueue schema compliance, Warden 503 circuit handling, IDOR session verification
  - `Document Management`: `GET /api/search/docs` summary & counts, `DELETE /api/search/docs` source pruning, `POST /api/search/docs/raw` note ingestion & chunking, `POST /api/search/docs/sync` reconciliation, and 500 error handling

### 4.3 Tier 3: React 19 Web UI (`searchboost_ui`)
- **Location:** `searchboost_ui/src/test/`
- **Framework:** Vitest, React Testing Library, jsdom
- **Test Count:** 59 Tests across 10 test files
- **Coverage Areas:**
  - `SearchPage`: Mode toggle interactions (`Deep Research` vs `Fast Answer`)
  - `SearchPage`: Web search switch interactions (`Web Search: ON` vs `OFF`)
  - `SearchPage`: All 4 toggle state permutations and dynamic badge rendering (`[🔬 Deep Research]`, `[⚡ Fast Answer]`, `[🌐 Web Search]`, `[🔌 Local Knowledge]`)
  - `KnowledgeBaseModal`: Document catalog overview, stats counters, file source deletion, raw note markdown ingestion, manual file sync trigger
  - `SearchBar`: Input handling, keyboard shortcuts (Ctrl+Enter), disabled states
  - `ResultDisplay`: Markdown code blocks, citation rendering, copy buttons
  - `AdminPage & Tables`: User management, role elevation modals
  - `Auth & ProtectedRoute`: Session redirection, unauthenticated gates

### 4.4 Tier 4: Python Worker Fleet (`searchboost_service`)
- **Location:** `searchboost_tests/unit_tests/`, `searchboost_tests/functional_tests/`
- **Framework:** Pytest, pytest-asyncio, unittest.mock
- **Test Count:** 48 Tests
- **Coverage Areas:**
  - `argparser`: CLI argument parsing, boolean string parsers, defaults
  - `handshake`: Warden `SearchRequest` schema compatibility
  - `ollama_client`: Embedding generation, chat completions, retry backoff
  - `document_service`: PostgreSQL `pgvector` CRUD, HNSW index verification, cosine distance search, source deletion, `list_sources_detailed`
  - `hybrid_rrf`: Dense vector + sparse BM25 PostgreSQL `tsvector` fusion via Reciprocal Rank Fusion ($k=60$), pure vector mode fallback
  - `watcher`: Automated file watcher daemon, hash-based change detection, incremental ingestion, source deletion synchronization, lifecycle management
  - `ingester`: Semantic recursive chunker, paragraph boundaries, code block preservation, Unicode/Emoji handling, zero-byte and missing file safety
  - `service`: Offline SearXNG bypass, hybrid meta-search synthesis, greeting short-circuiting
  - `e2e_matrix`: 4-mode operational verification, cache segregation, database error recovery

---

## 5. Execution Matrix & Continuous Integration

### 5.1 Local CI Execution Command
To execute the complete 157-test verification suite locally:
```bash
./scripts/ci_local.sh
```

### 5.2 GitHub Actions Pipeline (`.github/workflows/ci.yml`)
All pull requests and merges to `main` and `dev` automatically trigger the 4-tier pipeline:
1. `warden-check`: Runs on `[self-hosted, linux]` (Clippy, Format, 18 Rust tests)
2. `api-check`: Runs on `[self-hosted, linux]` (Lint, Typecheck, 32 Jest tests)
3. `ui-check`: Runs on `[self-hosted, linux]` (Vitest, 59 React tests, Production Build)
4. `worker-check`: Runs on `[self-hosted, linux]` (Pytest, 48 Python tests)

---

## 6. QA Sign-Off Criteria for Releases

A release build is certified ready for deployment when:
1. **Pass Rate:** 100% of tests pass across all 4 tiers (134/134).
2. **Linter & Type Cleanliness:** Zero Clippy warnings, zero Rustfmt errors, zero TypeScript errors.
3. **Zero Leaks:** Automated offline tests verify `mock_web_search.call_count == 0` when `web_search=false`.
4. **Cache Segregation:** Cache keys match regex `^(deep|fast):(web|local):.+`.
5. **No Cloud Spend:** All CI workflows execute entirely on self-hosted infrastructure.
