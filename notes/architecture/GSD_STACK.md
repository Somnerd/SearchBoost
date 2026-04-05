# Tech Stack

## Current Stack

- **API/Gateway (Node.js)**: TypeScript, Express, Prisma ORM
- **Sidecar Proxy (Rust)**: Axum, Tokio, Deadpool-Redis, Failsafe
- **Worker (Python)**: ARQ Queue, SQLAlchemy, AsyncIO
- **UI (React)**: TypeScript, Vite, Tailwind CSS
- **Data (Databases)**: PostgreSQL (pgvector extension), Redis

## Observation Layer

- **Logging (Rust)**: Tracing, tracing-subscriber
- **Logging (Python)**: logging (Debug/Metrics logging)

## Upcoming Migrations & Tools (Target Sprints)

- **Testing Infrastructure**: Jest & Supertest (API), E2E Containers
- **Transport Contracts**: Protobuf / gRPC
- **Embedded Database**: LanceDB (replacing pgvector for serverless Edge deployment)
- **Local Crawling**: Tantivy (Index), Firecrawl (Scraping Integrations)
- **Monitoring**: Prometheus / Grafana
- **Scaling / Cache**: Valkey (Linux Foundation Redis fork)
