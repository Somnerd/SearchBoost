# SearchBoost Engineering & Cooperation Standards

This document serves as the mandatory protocol for AI agents and collaborators working on the SearchBoost project. It prioritizes stability, security, and extreme awareness of production-grade quality.

---

## ✨ 1. The Showcase Standard (CV-Grade Quality)

This project is not a sandbox; it is a professional showcase and a core component of the creator's professional identity.

- **Gold Standard Logic**: Every fix must be architecturally sound. Avoid "hacks" or temporary patches.
- **Respect for Originality**: The core logic was built with the creator's "own two hands." Any modifications must respect and preserve the original intent and quality of that work.
- **The Pristine Rule**: Do not leave scratch scripts, unused `.env.*` files, or commented-out code blocks in the repository. Every commit must bring the branch closer to a "production-ready" state.

## 🛡️ 2. The 25-Minute Rule (Build Cycle Awareness)

Every code change that triggers a container rebuild (especially Rust/Warden) has a minimum cost of **25 minutes** (10m Review + 10m Build + 5m Testing).

- **BATCH** logic updates. Propose the entire system fix (API + Warden + Worker + UI) in one go.
- **VERIFY** logic mentally and with logs before requesting a build.
- **incremental/multi-stage aware**: Leverage Docker layer caching by keeping dependencies fixed unless a version bump is required.

## 🏗️ 3. Respect the "Working" State

If a component is described as "working fine" or "great even," it is considered **Read-Only**.

- **Do not refactor** working code for aesthetic reasons or "cleaner" signatures.
- **Adapt new code** to the existing working interfaces.
- If a change to a working component is truly necessary (e.g. for a security patch), it must be flagged with a **'CRITICAL SECURITY OVERHAUL'** prefix.

## 🤝 4. Secure-by-Default Protocol

SearchBoost enforces a strict security posture for all new contributions.

- **Fail-Closed Strategy**: Services (API, Warden, Worker) MUST crash on startup if required secrets (JWT_SECRET, DB_PASSWORD) are missing. NEVER use hardcoded fallbacks.
- **Non-Root Identity**: All newly added containers must run as unprivileged users (e.g., `node`, `nginx-unprivileged`).
- **Filesystem Lockdown**: Sensitive configuration files (`.env`) must be restricted to `chmod 600` via installation scripts.
- **Input Sanitization**: All SQL queries using `LIKE` must use the `ESCAPE` clause to prevent wildcard injection.

## 🤝 5. The "Handshake" Protocol (Propose Before Edit)

SearchBoost is a distributed system with cross-language serialization (Rust vs. Python vs. Node).

1. **Analyze**: Identify the failure in the handshake (JSON keys, Redis keys, Delimiters).
2. **Propose**: Detail the exact changes across all affected tiers (UI → API → Warden → Worker).
3. **Execute**: Once approved, apply changes as a single transaction to keep the stack synchronized.

## 🪵 6. The Gospel of Logging

Logs are the primary source of truth. Every request must be traceable from the React UI through the final Worker persistence.

- **Traceability**: All logs must include the `job_id` (e.g., `SB-SESSION:user:thread:uuid`).
- **Log Levels**: Use `DEBUG` for internal state and `INFO` for core lifecycle events.
- **The Log Collector**: Use `collect_logs.sh` before forming a hypothesis. Analysis must start with fresh multi-service logs.

## 🧪 7. Automated Verification

- **IDOR Harnesses**: Every update to the search proxy must be validated by the `test_idor.js` tool to prove cross-user boundaries are intact.
- **Regression Testing**: Fixes must be accompanied by a manual or automated test case in `MANUAL_TESTPLAN.md`.

---
*Updated on 2026-03-28 by Antigravity (Assistant) following the Phase 6 Security Audit.*
