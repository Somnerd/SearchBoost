# Contributing to SearchBoost

Thank you for your interest in contributing to **SearchBoost**! We welcome bug reports, feature requests, documentation improvements, and code contributions from developers of all skill levels.

---

## 🏛️ Architecture Overview

SearchBoost is structured into four distinct architectural tiers:

1. **Rust Warden Relay (`searchboost_warden`)**: High-throughput distributed proxy sidecar.
2. **TypeScript Express API (`searchboost_api`)**: Authentication, user session management, and RBAC gateway.
3. **React 19 Web UI (`searchboost_ui`)**: Modern frontend client built with Vite, TailwindCSS, and Lucide icons.
4. **Python Async Worker (`searchboost_service`)**: Background worker orchestrating SearXNG search retrieval and local LLM synthesis via Ollama.

> [!NOTE]
> **Data Privacy Invariant**: All Personally Identifiable Information (PII) masking, redaction, and compliance tokenization are strictly handled upstream by [IronWarden](https://github.com/Somnerd/IronWarden). SearchBoost processes clean search requests and contains no PII logic.

---

## 🛠️ Local Development & Quickstart

### Prerequisites
* **Docker & Docker Compose** (Recommended)
* **Node.js 20+** & `npm`
* **Rust (MSRV 1.82+)** with `cargo`, `clippy`, and `rustfmt`
* **Python 3.10+** with `pytest`

### Getting Started

```bash
# 1. Clone the repository
git clone https://github.com/Somnerd/SearchBoost.git
cd SearchBoost

# 2. Setup your local environment
cp .env.example .env

# 3. Start the entire container stack
docker compose up -d
```

---

## 🧪 Testing & CI Verification

Before submitting any Pull Request, you must verify all 4 tiers locally. We provide a single runner script that executes all unit, integration, and UI test suites:

```bash
./scripts/ci_local.sh
```

This verifies:
* **Tier 1 (Rust Warden)**: `cargo fmt --check`, `cargo clippy`, and `cargo test`.
* **Tier 2 (Express API)**: TypeScript type-check (`tsc --noEmit`) and Jest test suite.
* **Tier 3 (React 19 UI)**: Vitest component suite (45 tests) and production Vite build.
* **Tier 4 (Python Worker)**: Pytest unit and functional test suites.

---

## 🌿 Branching & Pull Requests

1. **Fork** the repository and create your branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Write clean, documented code** adhering to existing code styles:
   - Rust: `cargo fmt` and `cargo clippy -- -D warnings`
   - TypeScript: Follow existing ESLint rules
   - Python: Clean PEP 8 formatting
3. **Add tests** covering new endpoints, UI components, or worker logic.
4. **Open a Pull Request** against `main`:
   - Clearly describe what the PR accomplishes.
   - Reference any relevant issues.
   - Confirm that `./scripts/ci_local.sh` passes 100% cleanly.

---

## 📜 Code of Conduct

All contributors are expected to uphold the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).
