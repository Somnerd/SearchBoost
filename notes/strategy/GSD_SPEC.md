# Project Specification: Phase 7 - Production Rigor & Vector Search (FINALIZED)

## Goal
Harden the architecture for production deployment, implement semantic discovery (long-term memory), and enable horizontal scaling of the worker service.

## Requirements

### 1. Vector Search & Long-Term Memory (COMPLETED)
- **Persistence**: Store conversation turns with vector embeddings (pgvector).
- **Retrieval API**: API endpoint to search history based on semantic similarity.
- **Context Injection**: Worker service must retrieve and inject relevant historical context into research prompts.

### 2. Horizontal Scaling
- **Redis Task Locality**: Replace current local-only task management with Redis-backed distributed task queue logic if needed, or ensure the current `searchboost_rust` (Warden) can load-balance across multiple Python workers.
- **Worker Discovery**: The Warden proxy must be able to distribute tasks to multiple worker instances.
- **Statelessness**: Ensure workers do not rely on local disk for session state (use Redis/Postgres).

### 3. Production Hardening
- **Dynamic LLM Selection**: Allow the UI or request headers to override the Ollama model name used for research.
- **Health Checks**: Standardize Docker HEALTHCHECK instructions for all services.
- **Error Masking**: Ensure the production proxy masks raw backend stack traces with generic 503/500 errors.

## Success Criteria
- [x] Semantic history retrieval is integrated into the research loop.
- [ ] Multiple worker containers can be deployed and successfully handle separate concurrent requests.
- [ ] Research model can be changed dynamically without service restart.
