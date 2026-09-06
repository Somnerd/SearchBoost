# 🎯 SearchBoost Priority To-Do List

## 🔴 HIGH PRIORITY: BUILD SYSTEM OPTIMIZATION (Monday Kick-off)
*The 10-minute build cycle is currently our biggest blocker. We must solve this before continuing feature work.*

1.  **Multi-Stage Dockerfile Caching**: Refactor `searchboost_warden/Dockerfile` to cache dependencies separately from source code. (Target: < 2m rebuilds).
2.  **Dev-Mode Toggle**: Update `docker-compose.yml` to support standard `cargo build` (Debug) instead of `--release` for local development cycles.
3.  **Incremental Build Volumes**: Implement persistent volume mounting for the `target` directory to preserve compilation artifacts across container restarts.
4.  **Linker Upgrade**: Switch to the `mold` or `lld` linker inside the build stage to eliminate linking bottlenecks.

## 🟡 STABILIZATION & QUALITY
5.  **Test Suite Foundation**:
    - [ ] Create Redis mock for Warden unit tests.
    - [ ] Implement query payload validation tests for the Worker.
    - [ ] Build a "Sovereign Handshake" integration test script.
6.  **Engineering Manual Compliance**: Review all modules for "Showcase Standard" (CV-grade) quality and documentation.

## 🟢 FEATURE ROADMAP (On Hold until Optimization & Stabilization)
7.  **AI Orchestration Enhancements**: (Refining prompts and completion logic).
8.  **Redis Sharding Visualizer**: (Internal tool to verify session-based sharding).
9.  **Reddit Showcase Prep**: (Final cleanup for public announcement).
10. **Research Mode Toggle UI Button** ([Issue #46](https://github.com/Somnerd/SearchBoost/issues/46)): Add interactive toggle for Deep Multi-Step Research vs Fast Direct Answers.
11. **Web Search Toggle UI Button** ([Issue #47](https://github.com/Somnerd/SearchBoost/issues/47)): Add UI toggle to switch between Live SearXNG Web Retrieval and Pure Offline/Local LLM memory.

---
*Created on 2026-03-15. Dedicated to the "None-of-the-above" promise of speed and stability.*
