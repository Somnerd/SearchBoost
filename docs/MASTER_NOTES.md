# 🚀 SearchBoost: Master Technical Notes & Architectural Manual

**Project Name:** SearchBoost  
**Repository:** `Somnerd/SearchBoost`  
**License:** Transitioning to MIT License (*Copyright (c) 2026 Nikolas Alexandrakis*)  
**Core Technologies:** Rust 2021 (Axum, Tokio, Failsafe, Governor, Bollard), Node.js / TypeScript 5 (Express, Prisma), Python 3.10+ (ARQ, Redis, AsyncIO), PostgreSQL 16 (`pgvector`), SearXNG, Ollama, React 19 + Vite  

---

## 1. System Overview & Purpose

**SearchBoost** is an autonomous cognitive search, deep research, and vector grounding engine engineered with a resilience-first distributed architecture.

It bridges the gap between private LLM reasoning and real-time world knowledge:
1. **Intelligent Query Optimization:** Translates ambiguous natural language prompts into targeted keyword queries.
2. **Federated Meta-Search:** Aggregates and normalizes organic web snippets across dozens of search engines via an air-gapped SearXNG instance.
3. **Long-Term Vector Memory:** Ingests and recalls semantically similar conversation turns using PostgreSQL with `pgvector` (768-dimensional embeddings).
4. **Resilience Sidecar ("The Warden"):** A dedicated Rust proxy guarding databases and task queues via circuit breakers, rate limits, and container health observers.
5. **Privacy Gate:** Scans and blocks PII leakage before data touches semantic caches or external networks.

---

## 2. Multi-Tier Distributed Architecture

```
                                  ┌────────────────────────────┐
                                  │      React 19 + Vite       │
                                  │   (Search, History, Admin) │
                                  └─────────────┬──────────────┘
                                                │ HTTP / JWT Cookies
                                                ▼
                                  ┌────────────────────────────┐
                                  │    TypeScript API (3001)   │
                                  │ (Express 5, Prisma, pgvector)
                                  └──────┬───────────────┬─────┘
                                         │               │ HTTP (/enqueue, /results)
               Prisma / Relational & Vec │               ▼
                                         │ ┌───────────────────────────┐
                                         │ │ Rust Warden Relay (14141) │
                                         │ │ • Failsafe Circuit Breaker│
                                         │ │ • Governor Rate Limiter   │
                                         │ │ • Bollard Docker Observer │
                                         │ └─────────────┬─────────────┘
                                         │               │
                                         ▼               │ Redis ARQ Task Queue
                            ┌─────────────────────────┐  ▼
                            │ PostgreSQL 16 (pgvector)│ ┌──────────────┐
                            │ • users & auth          │ │  Redis 7.4   │
                            │ • threads (sessions)    │ │ • arq:queue  │
                            │ • conversation_turns    │ │ • sb:result  │
                            └─────────────────────────┘ └──────┬───────┘
                                                               │
                                                               │ Pop Research Jobs
                                                               ▼
                                                ┌──────────────────────────────┐
                                                │      Python ARQ Worker       │
                                                │  (Ollama + SearXNG Pipeline) │
                                                └──────────────────────────────┘
```

---

## 3. Component Details & Technical Specifications

### 3.1 The Rust Warden (`searchboost_warden`)
- **Port:** `14141`
- **Modules:**
  - `main.rs`: Entry point, retry loops with `tokio_retry`, thread pools, and shutdown lifecycle.
  - `relay.rs`: Axum 0.7 HTTP relay exposing `/health`, `/enqueue`, and `/results/:job_id`.
  - `breaker.rs`: Configures the `failsafe` circuit breaker. Automatically sheds load when upstream dependencies fail.
  - `configurator.rs`: Loads environment variables and YAML settings with graceful defaults.
  - `observer.rs`: Real-time Docker log streaming via `bollard` inspecting worker containers with label `com.searchboost.service=worker`.

### 3.2 The Backend API (`searchboost_api`)
- **Port:** `3001`
- **Runtime:** Node.js 20, TypeScript 5.4, Express 5.
- **ORM:** Prisma 5.14 with binary targets `native`, `debian-openssl-3.0.x`, and `linux-musl`.
- **Security:** Bcrypt (12 salt rounds), HTTP-only cookies, JWT verification, and strict IDOR session validation.

### 3.3 The Research Worker (`searchboost_service`)
- **Queue System:** ARQ (Async Redis Queue).
- **Execution Pipeline:**
  1. `cache.get_cached_response(query)`: Instant cache hit check.
  2. `ai_handler.query_LLM(reason="optimization")`: Optimizes search query keywords.
  3. `pii_detector.scan(query)`: Regex safety gate for payment cards, SSNs, IBANs, and emails.
  4. `web_search.searxng_search()`: Retrieves top 5 normalized search snippets.
  5. `context_service.search_relevant_history()`: Injects semantically similar past turns.
  6. `ai_handler.query_LLM(reason="research")`: Produces cited, grounded synthesis.
  7. `cache.cache_response()` & `persistence_service.save_turn()`: Commits to Redis and `pgvector`.

---

## 4. Relationship with IronWarden (The Sovereign Sister System)

| Feature | SearchBoost | IronWarden |
| :--- | :--- | :--- |
| **Primary Role** | Cognitive Search & Vector Grounding | Privacy Shield & Security Gateway |
| **Relay Port** | `14141` | `14141` |
| **Session Shard Format**| `SB-SESSION:{user}:{thread}:{uuid}` | `SB-SESSION:{user}:{thread}:{uuid}` |
| **Payload Schema** | `{ query, thread_id, username, options }` | `{ query, thread_id, username, options }` |
| **Storage Engine** | PostgreSQL 16 (`pgvector`) + Redis | SQLite (Audits) + LanceDB (Embeddings) |
| **Target Audience** | Research, Enterprise Grounding, Agents | Healthcare, Finance, Regulatory Compliance |

---

## 5. Ongoing Execution & Sprint Progress

- [x] Cloned and synchronized latest `origin/main` (56 commits ahead).
- [x] Closed 4 stale/duplicate PRs (#14, #18, #20, #24) and deleted branches.
- [x] Closed 5 completed milestone issues (#25, #26, #27, #28, #29).
- [x] Created GitHub Actions CI pipeline (`.github/workflows/ci.yml`).
- [ ] Rust Warden Clippy, Format & Test hardening (Subagent 1 in progress).
- [ ] Python CLI Handshake & Test expansion (Subagent 2 in progress).
- [ ] Transition License to MIT across workspace.
- [ ] Revamp `README.md` with visual architecture diagram and hiring hooks.
