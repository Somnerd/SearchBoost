# Project Specification: Phase 8 - The Safety Net & Strict Contracts

## Goal

To abandon the unmaintainable prototype assumptions by replacing fragile "Magic String" communications with definitive cross-language contracts, and establish a foundational automated testing strategy.

## Requirements

### 1. Unified Interface Definitions (gRPC / Protobuf)

- **Standardization**: All object handshakes between Node.js, Rust, and Python must strictly utilize Protobuf definitions.
- **Vulnerability Patch**: The current reliance on parsing `SB-SESSION:user:uuid` prefix-delimiter strings must be eradicated across all source vectors, mitigating subtle IDOR edge-case risks.

### 2. E2E Safety Scaffolding

- **Verification Coverage**: The `jest` and `supertest` scaffolding implemented in Phase 7 must assert actual system state. Scaffolds using tautologies (e.g. `expect(true).toBe(true)`) must be replaced with a minimum of 80% route coverage testing inside the `/searchboost_api` module.

### 3. Warden Observability Upgrades

- **Circuit Telemetry**: Warden's integrated `failsafe` library states must be directly exported via a `/metrics` Prometheus endpoint, enabling external infrastructure monitoring tools (Grafana) to assess whether the Sidecar is actively holding a closed protection boundary during LLM stress-loads.

## Success Criteria

- [ ] Core services interact entirely via compiled Protobuf schema objects instead of arbitrary JSON or Python Pickles.
- [ ] Running `docker-compose -f docker-compose.test.yml run e2e_runner` yields valid, passing unit-integration results for API endpoints.
- [ ] A dedicated Prometheus scraper can passively read the `searchboost_warden/health` and `/metrics` paths to aggregate request volumes and proxy breaker-status.
