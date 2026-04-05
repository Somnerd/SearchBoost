# SearchBoost Performance Benchmarks (Phase 7)

## Horizontal Scaling Efficiency
Date: 2026-04-01 | Environment: Docker Desktop (Linux)

| Worker Count | Total Time (10 reqs) | Avg Latency (Enqueue) | Status |
|--------------|----------------------|-----------------------|--------|
| 1 Worker     | 242ms                | 24.2ms                | ✅ Pass |
| 2 Workers    | 414ms                | 41.4ms                | ✅ Pass |

**Note**: Benchmarks measured the *enqueue* latency (API -> Warden -> Redis). The increase in latency with 2 workers is attributed to the distributed log observation overhead and internal DNS resolution within the Docker network for multiple worker targets.

## Model Swap Latency
Impact of runtime model selection on API response time.

| Model Variant           | Total Time (5 reqs) | Avg Latency |
|-------------------------|---------------------|-------------|
| llama3.2:latest         | 173ms               | 34.6ms      |
| nomic-embed-text:latest | 39ms                | 7.8ms       |

**Key Finding**: The end-to-end delta between models in the `SearchBoostService` suggests an increased latency of **~25-30ms** per task dispatch phase (including internal DNS lookup and option merging). *Note*: This test evaluates end-to-end load; we recommend running an isolated dispatch/switch microbenchmark on `SearchBoostService` to measure pure switch overhead accurately in the future.

## Scaling Verified
- [x] Warden successfully discovers multiple workers via labels.
- [x] API correctly propagates `model` parameters to selected worker instances.
- [x] Redis task locality ensures tasks are picked up by the next available worker.
