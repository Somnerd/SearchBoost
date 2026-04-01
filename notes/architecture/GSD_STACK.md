# Technology Stack

> Phase 7: Distributed & Semantic Infrastructure Registry

## Runtime

| Technology | Version | Purpose |
|------------|---------|---------|
| Node.js | v20-Alpine | Authenticated REST API (Non-root `node` user) |
| Rust | 1.93.1 | High-performance Warden Proxy / rate-limiter |
| Python | 3.11 | ARQ Worker executing intensive LLM research loops |
| Nginx-Unprivileged| Stable-Alpine | Secure frontend delivery on non-root Port 8080 |

## Production Dependencies

| Package | Ecosystem | Purpose |
|---------|---------|---------|
| express, pg, bcrypt | npm | JWT Auth and PostgreSQL conversation mapping |
| jsonwebtoken | npm | Secure cookie-based session management |
| tokio, axum | cargo | Asynchronous Rust API framework |
| tower_governor | cargo | GCRA rate-limiting (25 req/s per user) |
| bollard | cargo | Docker API client for dynamic worker discovery |
| arq, asyncpg, redis | pip | High-speed task queue and ACID database persistence |
| pydantic-settings | pip | Recursive deep-merge configuration validation |

## Infrastructure

| Service | Provider | Purpose |
|---------|----------|---------|
| PostgreSQL 16 + pgvector | DB Engine | Relational persistence + Vector similarity for Chat History |
| Redis 7.4-Alpine | Memory Cache | Authenticated Semantic TTL Caching + ARQ Job Queue |
| SearXNG | Web Fetcher | Distributed meta-search proxy returning JSON metadata |
| Ollama | LLM Engine | Local model execution (llama3.2) for private research |

## Configuration & Security

| Variable | Purpose | Required |
|----------|---------|----------|
| JWT_SECRET | Root signing key for user tokens | **YES** (Fail-Closed) |
| DB_PASSWORD | PostgreSQL access credential | **YES** |
| REDIS_PASSWORD | Redis AUTH credential | **YES** |
| MASTER_CONFIG_PATH| Base YAML configuration root | No (defaults to /configs) |
| SB_INSTANCE_IP | Target deployment IP for testplan resolution | No |

### Security Policies

- **File Permissions**: `.env` strictly enforced at `600`.
- **Identity Isolation**: Colons used as delimiters (`SB-SESSION:user:thread`) to prevent name-prefix collisions.
- **Rootless Execution**: 100% of application containers run as unprivileged users.
