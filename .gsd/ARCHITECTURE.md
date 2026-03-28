# Architecture

> Updated to Phase 6: Post-Audit Security Hardening

## Overview
SearchBoost is a decentralized, highly-resilient hybrid-AI search engine pipeline. It is architected as an asynchronous distributed system isolating user authorization (Node.js), high-throughput boundary ingress/caching (Rust), intensive LLM background execution (Python), and frontend client rendering (React). The system is **Secure-by-Default**, enforcing fail-closed configuration and unprivileged container execution.

## System Diagram
```
[ User Browser (React Vite) ]
          │
      (HTTP / JWT / HttpOnly Cookie)
          ▼
[ Express API (Node.js) ] ───────▶ [ PostgreSQL DB (Auth & History) ]
          │
     (Network Relay / Colon-Delimited ID)
          ▼
[ Warden Proxy (Rust) ] ─────────▶ [ Redis (Cache & Enqueue) ]
          │
    (ARQ Polling / Pickle Serialization)
          ▼
[ Worker Instance (Python) ] ────▶ [ PostgreSQL DB ]
          │
    ┌─────┴──────┐
    ▼            ▼
[ Ollama ]   [ SearXNG ]
```

## Components

### React Web Client 
- **Purpose:** Interactive GUI for concurrent search threads and authentications.
- **Location:** `searchboost_ui/`
- **Security:** CSRF protection via HttpOnly cookies; no client-side JWT access.

### Node.js REST API 
- **Purpose:** Manages User Identity (JWT), maps database Session Threads using colon-delimited unique identifiers (`SB-SESSION:user:thread`), and securely proxies queries to Warden.
- **Location:** `searchboost_api/`
- **Security:** Runs as non-root `node` user. Enforces strict `Fail-Closed` startup (crashes if JWT_SECRET is missing).

### Rust Warden Proxy
- **Purpose:** Ingress Gateway serving high-speed Semantic Cache lookups. Runs strict `tower_governor` GCRA rate-limiting (25 req/s) and Circuit Breaking.
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
| Redis | Memory DB | Semantic TTL Caching + High Speed Job Queue (Authenticated) |
| PostgreSQL | Relational DB | ACID compliance over Account Usernames and Historical Chat states |

## Conventions
- **Naming:** Consistent snake_case for services (`sb_warden`, `sb_worker`), kebab-case for generic dependencies (`sb-searxng`).
- **Security Policy:** All containers run as unprivileged users. Permissions on `.env` are restricted to `600`.
- **Testing:** Driven by IDOR verification harnesses and Phase-specific validation plans.
- **Configuration:** Hierarchical YAML fallback logic with recursive deep-merging.

## Technical Debt
- [ ] Implement robust error-recovery for PostgreSQL connection loss in Python Workers.
- [ ] Add rate-limit metrics exposure (Prometheus) to the Warden sidecar.
