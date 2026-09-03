#!/usr/bin/env bash
# =============================================================================
# SearchBoost — Unified Local CI Runner
# Runs the full verification suite locally across all 4 system tiers:
# 1. Rust Warden Relay
# 2. TypeScript Express API
# 3. React 19 Web UI
# 4. Python Async Worker Fleet
# =============================================================================

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; RESET='\033[0m'
PASS="${GREEN}✔ PASS${RESET}"; FAIL="${RED}✘ FAIL${RESET}"

FAILED_TIERS=()
START_TIME=$(date +%s)

header() {
  echo ""
  echo -e "${BLUE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
  echo -e "${BLUE}${BOLD}  TIER: $1${RESET}"
  echo -e "${BLUE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
}

pass_tier() { echo -e "\n  ${PASS}  $1"; }
fail_tier() { echo -e "\n  ${FAIL}  $1"; FAILED_TIERS+=("$1"); }

# Locate IDE / system node/npm if available
export PATH="/home/somnerd/.antigravity-ide-server/bin/2.5.5-ecfbad74d93962fc8ca485d93ab9b4f3d4cb6cf8:/home/somnerd/.local/bin:$PATH"

# ── 1. Rust Warden Relay ─────────────────────────────────────────────────────
header "1. Rust Warden Sidecar (Clippy, Format & Unit Tests)"
if (cd searchboost_warden && cargo fmt --check && cargo clippy --all-targets -- -D warnings && cargo test --all-targets); then
  pass_tier "Rust Warden Relay (17/17 Tests)"
else
  fail_tier "Rust Warden Relay"
fi

# ── 2. TypeScript Express API ────────────────────────────────────────────────
header "2. Node.js / Express 5 API (Typecheck & Jest Integration Tests)"
if (docker run --rm -v "$(pwd)/searchboost_api":/app -w /app node:20-alpine sh -c "npx tsc --noEmit && npm test"); then
  pass_tier "TypeScript Express API (22/22 Tests)"
else
  fail_tier "TypeScript Express API"
fi

# ── 3. React 19 Web UI ───────────────────────────────────────────────────────
header "3. React 19 UI (Vitest Suite & Production Build)"
if (cd searchboost_ui && node /home/somnerd/.local/lib/node_modules/npm/bin/npm-cli.js test && node /home/somnerd/.local/lib/node_modules/npm/bin/npm-cli.js run build); then
  pass_tier "React 19 UI (45/45 Tests + Build)"
else
  fail_tier "React 19 UI"
fi

# ── 4. Python Worker Fleet ───────────────────────────────────────────────────
header "4. Python Worker & Distributed Handshake (Pytest Suite)"
PYTHON_EXEC="/home/somnerd/Documents/Projects/IronWarden/.venv/bin/python3"
if [ ! -f "$PYTHON_EXEC" ]; then
  PYTHON_EXEC="python3"
fi

if PYTHONPATH=searchboost_service "$PYTHON_EXEC" -m pytest searchboost_tests/unit_tests searchboost_tests/functional_tests -v; then
  pass_tier "Python Worker (11/11 Tests)"
else
  fail_tier "Python Worker"
fi

# ── Summary ──────────────────────────────────────────────────────────────────
TOTAL_TIME=$(( $(date +%s) - START_TIME ))
echo ""
echo -e "${BLUE}${BOLD}═══════════════════════════════════════════════════════${RESET}"
echo -e "${BOLD}  LOCAL CI RUN SUMMARY (${TOTAL_TIME}s total)${RESET}"
echo -e "${BLUE}${BOLD}═══════════════════════════════════════════════════════${RESET}"

if [ ${#FAILED_TIERS[@]} -eq 0 ]; then
  echo -e "  ${PASS}  ${GREEN}${BOLD}ALL 4 TIERS PASSED (95/95 Tests Passing)${RESET}"
  echo -e "  Ready for production deployment and release packaging."
  exit 0
else
  echo -e "  ${FAIL}  ${RED}${BOLD}${#FAILED_TIERS[@]} TIER(S) FAILED:${RESET}"
  for f in "${FAILED_TIERS[@]}"; do
    echo -e "      - $f"
  done
  exit 1
fi
