#!/usr/bin/env bash
# =============================================================================
# SearchBoost — Graceful Teardown & Port Release Utility
# =============================================================================

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

SYNERGY_MODE=false
EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
  case $1 in
    --with-ironwarden|--synergy)
      SYNERGY_MODE=true
      shift
      ;;
    -v|--volumes)
      EXTRA_ARGS+=("-v")
      shift
      ;;
    *)
      EXTRA_ARGS+=("$1")
      shift
      ;;
  esac
done

echo -e "${CYAN}Stopping SearchBoost container fleet...${NC}"
docker compose down "${EXTRA_ARGS[@]}"

if [ "$SYNERGY_MODE" = true ]; then
  IW_DIR="$ROOT_DIR/../IronWarden"
  if [ -d "$IW_DIR" ] && [ -f "$IW_DIR/docker-compose.yml" ]; then
    echo -e "${CYAN}Stopping sibling IronWarden container stack...${NC}"
    (cd "$IW_DIR" && docker compose down "${EXTRA_ARGS[@]}")
  fi
fi

echo -e "${GREEN}✔ Stack teardown complete. All allocated ports released.${NC}"
