# Architecture

> Updated to Phase 7: Distributed Observation & Semantic Search

## Overview
SearchBoost is a decentralized, resilient hybrid-AI search engine pipeline. It is architected as an asynchronous distributed system isolating user authorization (Node.js), observability-driven gateway (Rust), resource-intensive background execution (Python), and frontend client rendering (React). The system now supports horizontal scaling of workers via label-based discovery and deep semantic persistence using vector embeddings.

## System Diagram
```text
[ User Browser (React Vite) ]
│
(HTTP / JWT / HttpOnly Cookie)
▼
[ Express API (Node.js) ] ───────▶ [ PostgreSQL (Auth & Semantic History) ]
│                                  └─▶ (pgvector extension)
(Network Relay / Job Delegation)
▼
[ Warden Proxy (Rust) ] ─────────▶ [ Redis (Cache & Enqueue) ]
│                                  └─▶ (Label-based Worker Discovery) 
(ARQ Tasking / Dynamic Model Injected)
▼
[ Worker Instances (Python x N) ] ──▶ [ PostgreSQL DB ]
│
┌─────┴──────┐
▼            ▼
[ Ollama ]   [ SearXNG ]
```


## Components


### React Web Client
- **Purpose:** Interactive GUI for concurrent search threads and authentications.
- **Location:** `searchboost_ui/`
- **Security:** XSS protection via HttpOnly cookies (hides JWT from scripts); CSRF mitigation via `Strict` SameSite policy.


### Node.js REST API
- **Purpose:** Manages User Identity (JWT), maps database Session Threads using colon-delimited unique identifiers (`SB-SESSION:user:thread`), and securely proxies queries to Warden.
- **Location:** `searchboost_api/`
- **Security:** Runs as non-root `node` user. Enforces strict `Fail-Closed` startup (crashes if JWT_SECRET is missing).


### Rust Warden Proxy
- **Purpose:** Ingress Gateway serving high-performance Semantic Cache lookups and real-time worker fleet observation. Discovers workers via Docker labels and streams logs to centralized audit files.
- **Location:** `searchboost_warden/`
- **Security:** Authenticates to Redis via environment secrets. Validates `job_id` segments to prevent IDOR traversal.


### Python ARQ Worker
- **Purpose:** Executes heavy I/O loops against Ollama for semantic reduction.
- **Location:** `searchboost_service/`
- **Security:** PII-Gate implemented via `PIIDetector` (triple-pass scan). Recursive deep-merge configuration logic with `CLI > ENV > YAML` precedence.


## Data Flow
1. User logs in safely via Node.js (`/api/auth/login`).
2. Search triggers dispatch via `Axios` passing secure session cookies.
3. Node constructs a **session_id** prefix (`SB-SESSION:${username}:${thread_id}`) and dispatches the query to the Rust `Warden`.
4. Warden generates a unique **job_id** by appending a UUID to the session prefix and enqueues the task in Redis.
5. Python pulls task, aggregates SearXNG metadata, prompts Ollama, maps the result to Postgres, and updates the Job ID status to `complete` in Redis.
6. React Client polls Warden via Node Proxy; Node validates result ownership before returning data.


## Integration Points
| External Service | Type | Purpose |
|------------------|------|---------|
| SearXNG | HTTP Engine | Open-Source Meta-Search proxy returning clean JSON bypassing bot-bans |
| Ollama | REST API | Local execution environment parsing open-weights |
| Redis | Memory DB | Semantic TTL Caching + High-Speed Job Queue (Authenticated) |
| PostgreSQL | Relational DB | ACID compliance over Account Usernames and Historical Chat states |


## Conventions
- **Naming:** Consistent snake_case for services (`sb_warden`, `sb_worker`), kebab-case for generic dependencies (`sb-searxng`).
- **Security Policy:** All containers run as unprivileged users. Permissions on `.env` are restricted to `600`.
- **Testing:** Driven by IDOR verification harnesses and Phase-specific validation plans.
- **Configuration:** Hierarchical YAML fallback logic with recursive deep-merging.


## Technical Debt
- [ ] Implement robust error-recovery for PostgreSQL connection loss in Python Workers.
- [ ] Add rate-limit metrics exposure (Prometheus) to the Warden sidecar.
