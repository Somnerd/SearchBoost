# Architecture

> Updated to Phase 7: Death Audit Resilience

## Overview

SearchBoost is a decentralized, resilient hybrid-AI search engine pipeline. It is architected as an asynchronous distributed system isolating user authorization (TypeScript/Node.js), observability-driven gateway (Rust), resource-intensive background execution (Decoupled Python Services), and frontend client rendering (React). The system supports horizontal scaling of workers via label-based discovery, deep semantic context injection, and is designed for zero-ops local deployment paths alongside secure enterprise environments.

## System Diagram

```text
[ User Browser (React Vite) ]
│
(HTTP / JWT / HttpOnly Cookie)
▼
[ Express API (TypeScript) ] ────▶ [ PostgreSQL (Auth & Semantic History via Prisma) ]
│                                  
(Protobuf/gRPC Target Phase 8)
▼
[ Warden Proxy (Rust) ] ─────────▶ [ Redis/Valkey (deadpool Connection Pool) ]
│                                  └─▶ (Label-based Worker Discovery) 
(ARQ Tasking)
▼
[ Cache / Context Services ] ────▶ [ PostgreSQL pgvector (Target: LanceDB Phase 9) ]
│ (Isolated Python Workers)
┌─────┴──────┐
▼            ▼
[ Ollama ]   [ SearXNG ]
```

## Components

### React Web Client
- **Purpose:** Interactive GUI for concurrent search threads and authentications.
- **Location:** `searchboost_ui/`

### TypeScript REST API (Node.js)
- **Purpose:** Manages User Identity (JWT), leverages Prisma ORM for type-safe database queries, and securely proxies requests to Warden.
- **Location:** `searchboost_api/`
- **Security:** Strict type boundaries. No string concatenation for SQL queries.

### Rust Warden Proxy
- **Purpose:** Ingress Gateway serving high-performance Semantic Cache lookups and real-time worker fleet observation.
- **Location:** `searchboost_warden/`
- **Resilience:** Implements `tokio-retry` exponential backoff for database connection safety, and `deadpool-redis` to negate connection churn overhead. Failed IDOR checks map to safe HTTP 503/403 responses instead of internal panics.

### Python Service Fleet (Decoupled)
- **Purpose:** Executes heavy I/O loops against Ollama for semantic reduction.
- **Location:** `searchboost_service/`
- **Architecture:** Separated concerns. The core logic relies on dedicated `ContextService` instances for assembling semantic history and `CacheService` instances for deduplicating LLM requests.

## Data Flow
1. User logs in safely via the TypeScript Node API setup (`/api/auth/login`).
2. Express issues queries utilizing validated schemas.
3. API dispatches the query to the Rust `Warden`.
4. Warden securely processes tasks relying on verified connection pools tracking job limits, eliminating panic vectors.
5. Python workers execute the workflow, transparently yielding specific HTTP timeout errors and logic traces instead of globally swallowing standard exceptions.

## Known Technical Debt & Risks

- **The Distributed Monolith Tax**: Because the system is heavily distributed, a simple chat sequence incurs multiple network hops across Redis just for internal tasking. Future iterations (e.g. gRPC ports) must minimize internal latency parsing.
- **Prisma Memory Bloat**: Running a full Prisma Query Engine binary inside a Node container for a basic 4-table schema is memory-heavy. Moving the stack directly to `LanceDB` in Phase 9 will relieve this.
- **Magic String Demarcation**: System currently relies on delimited IDs (`SB-SESSION:user:uuid`). Moving to strict Protobuf contracts (Phase 8) will solidify typings universally across language boundaries across workers.
