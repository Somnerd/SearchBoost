## 📝 Description
<!-- Briefly describe the purpose of this change, bug fix, or feature. -->

## 🔗 Related Issues & Work Packages
<!-- Link any related GitHub issues or work packages (e.g. Fixes #44, Fixes #45) -->

## 🛠️ Type of Change
- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 🔒 Security fix (hardens security invariants or fixes vulnerabilities)
- [ ] ⚡ Performance improvement
- [ ] 📚 Documentation update
- [ ] 🧹 Refactoring / Code cleanup

## 🛡️ SearchBoost System Invariants
Please verify that your change preserves system reliability:
- [ ] **Port Isolation:** Respects sovereign default ports (UI: 3000, API: 3001, Warden: 14142, Redis: 6380, SearXNG: 8888, Postgres: 5432, Ollama: 11434).
- [ ] **JSON Serialization:** Uses standardized UTF-8 JSON for Redis task queues (no Python pickle).
- [ ] **Zero-Trust IDOR:** Enforces user ownership checks across threads and vector memory.
- [ ] **Circuit Breaker:** Respects Warden fail-closed circuit health.

## ✅ Pre-Merge Checklist
- [ ] Rust Warden tests pass (`cargo test` in `searchboost_warden`)
- [ ] Python worker fleet tests pass (`pytest searchboost_tests`)
- [ ] Shell scripts validated (`bash -n scripts/*.sh`)
- [ ] No hardcoded secrets, keys, or credentials committed
- [ ] Documentation updated (`README.md`, `.env.example`, etc. if applicable)
