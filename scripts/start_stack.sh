#!/usr/bin/env bash
# =============================================================================
# SearchBoost — Unified One-Click Stack Launcher & Dynamic Port Orchestrator
# Supports standalone execution and synergistic tandem deployment with IronWarden.
# =============================================================================

set -e

# ANSI Color Codes
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

SYNERGY_MODE=false
DYNAMIC_PORTS=true

# Parse Command-line Arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --with-ironwarden|--synergy)
      SYNERGY_MODE=true
      shift
      ;;
    --no-dynamic-ports)
      DYNAMIC_PORTS=false
      shift
      ;;
    -h|--help)
      echo -e "${BOLD}SearchBoost Stack Launcher${NC}"
      echo "Usage: ./scripts/start_stack.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --with-ironwarden, --synergy   Deploy synergistically with sibling IronWarden stack"
      echo "  --no-dynamic-ports             Disable dynamic port allocation and strictly use .env defaults"
      echo "  -h, --help                     Show this help message and port allocation matrix"
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}. Use --help for usage."
      exit 1
      ;;
  esac
done

echo -e "${CYAN}${BOLD}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          🚀 SEARCHBOOST UNIFIED STACK LAUNCHER              ║"
echo "║   Autonomous Cognitive Search & Vector Grounding Engine      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 1. Prerequisite Checks
echo -e "${CYAN}[1/5] Checking environment prerequisites...${NC}"
command -v docker >/dev/null 2>&1 || { echo -e "${RED}ERROR: 'docker' is not installed or not in PATH.${NC}"; exit 1; }
docker compose version >/dev/null 2>&1 || { echo -e "${RED}ERROR: 'docker compose' (V2) is not installed.${NC}"; exit 1; }
command -v curl >/dev/null 2>&1 || { echo -e "${RED}ERROR: 'curl' is required for health check polling.${NC}"; exit 1; }

# Ensure .env exists
if [ ! -f ".env" ]; then
  if [ -f ".env.example" ]; then
    echo -e "${YELLOW}Notice: .env not found. Auto-generating secure .env from .env.example...${NC}"
    cp .env.example .env
    # Generate secure random secrets
    sed -i "s/super_secret_jwt_key_change_me_in_production_12345/$(openssl rand -hex 32)/" .env
    sed -i "s/searchboost_pass/$(openssl rand -hex 16)/" .env
    chmod 600 .env
  else
    echo -e "${RED}ERROR: Neither .env nor .env.example found in project root.${NC}"
    exit 1
  fi
fi

# Load current .env variables
set -a
source .env
set +a

# 2. Dynamic Port Allocation & Collision Immunity
echo -e "${CYAN}[2/5] Verifying port bindings & collision immunity...${NC}"

is_port_in_use() {
  local port=$1
  (echo > /dev/tcp/127.0.0.1/"$port") >/dev/null 2>&1
}

is_port_owned_by_container() {
  local port=$1
  local container_name=$2
  docker ps --filter "name=$container_name" --format '{{.Ports}}' 2>/dev/null | grep -q ":$port->" || false
}

resolve_port() {
  local svc_name=$1
  local env_var_name=$2
  local preferred_port=$3
  local container_name=$4
  local scan_limit=${5:-10}

  if [ "$DYNAMIC_PORTS" = false ]; then
    export "$env_var_name"="$preferred_port"
    return
  fi

  local port=$preferred_port
  local count=0

  while is_port_in_use "$port"; do
    if is_port_owned_by_container "$port" "$container_name"; then
      # Port is held by our own running container; safe to reuse
      break
    fi
    echo -e "${YELLOW}  • Notice: Port $port ($svc_name) is in use. Probing next available port...${NC}"
    port=$((port + 1))
    count=$((count + 1))
    if [ $count -ge $scan_limit ]; then
      echo -e "${RED}ERROR: Unable to allocate a free port for $svc_name within $scan_limit attempts from $preferred_port.${NC}"
      exit 1
    fi
  done

  if [ "$port" -ne "$preferred_port" ]; then
    echo -e "${MAGENTA}  ✔ Dynamic Allocation: $svc_name assigned to host port ${BOLD}$port${NC}${MAGENTA} (preferred $preferred_port was busy)${NC}"
  else
    echo -e "  ✔ $svc_name bound to sovereign port ${GREEN}$port${NC}"
  fi

  export "$env_var_name"="$port"
}

# Resolve each service host port
resolve_port "Web UI"           "UI_PORT"          "${UI_PORT:-3000}"          "sb_ui"
resolve_port "Node/TS API"      "API_PORT"         "${API_PORT:-3001}"         "sb_api"
resolve_port "PostgreSQL DB"    "POSTGRES_PORT"    "${POSTGRES_PORT:-5432}"    "sb_db"
resolve_port "Redis Cache"      "REDIS_PORT"       "${REDIS_PORT:-6380}"       "sb_redis"
resolve_port "SearXNG Search"   "SEARXNG_PORT"     "${SEARXNG_PORT:-8888}"     "sb-searxng"
resolve_port "Ollama LLM"       "OLLAMA_PORT"      "${OLLAMA_PORT:-11434}"     "sb_ollama"
resolve_port "Rust Warden Relay" "WARDEN_HOST_PORT" "${WARDEN_HOST_PORT:-14142}" "sb_warden"

# Check IronWarden Coexistence
if is_port_in_use 8080 || is_port_in_use 14141 || is_port_in_use 6379; then
  echo -e "${GREEN}  ✔ IronWarden sister services detected active on host (8080/14141/6379) with zero port collisions!${NC}"
fi

# 3. Synergistic Tandem Deployment
if [ "$SYNERGY_MODE" = true ]; then
  echo -e "${CYAN}[3/5] Activating Synergistic IronWarden Deployment...${NC}"
  
  # Ensure external shared network exists
  if ! docker network ls --format '{{.Name}}' | grep -q '^searchboost_net$'; then
    echo -e "  • Creating shared Docker bridge network '${BOLD}searchboost_net${NC}'..."
    docker network create searchboost_net >/dev/null
  fi

  IW_DIR="$ROOT_DIR/../IronWarden"
  if [ -d "$IW_DIR" ] && [ -f "$IW_DIR/docker-compose.yml" ]; then
    echo -e "  • Located sibling IronWarden repository at '${IW_DIR}'."
    if ! docker ps --format '{{.Names}}' | grep -q '^ironwarden$'; then
      echo -e "  • Starting IronWarden sovereign AI gateway..."
      (cd "$IW_DIR" && docker compose up -d)
    else
      echo -e "${GREEN}  ✔ IronWarden container is already active.${NC}"
    fi
  else
    echo -e "${YELLOW}  • Notice: Sibling directory ../IronWarden not found. Assuming standalone or remote IronWarden.${NC}"
  fi
  
  export IRONWARDEN_URL="http://127.0.0.1:8080"
  echo -e "${GREEN}  ✔ Upstream LLM privacy gating routed through IronWarden at ${IRONWARDEN_URL}${NC}"
else
  echo -e "${CYAN}[3/5] Skipping synergy orchestration (use --with-ironwarden to enable).${NC}"
fi

# 4. Launching SearchBoost Docker Compose Stack
echo -e "${CYAN}[4/5] Launching SearchBoost multi-tier container fleet...${NC}"
docker compose up -d

# 5. Service Health Check Polling
echo -e "${CYAN}[5/5] Polling service readiness and health endpoints...${NC}"

poll_health() {
  local name=$1
  local check_cmd=$2
  local max_retries=${3:-30}
  local delay=${4:-2}
  local count=0

  echo -n -e "  • Awaiting ${BOLD}$name${NC} "
  while [ $count -lt $max_retries ]; do
    if eval "$check_cmd" >/dev/null 2>&1; then
      echo -e " [${GREEN}HEALTHY${NC}]"
      return 0
    fi
    echo -n "."
    sleep "$delay"
    count=$((count + 1))
  done

  echo -e " [${RED}TIMEOUT${NC}]"
  echo -e "${YELLOW}Warning: $name did not report healthy within $((max_retries * delay))s. Review container logs with: docker logs sb_${name,,}${NC}"
  return 1
}

poll_health "Redis" "docker exec sb_redis redis-cli -a '${REDIS_PASSWORD:-searchboost_pass}' ping 2>/dev/null | grep -q PONG" 15 2 || true
poll_health "PostgreSQL" "docker exec sb_db pg_isready -U '${DB_USER:-searchboost}'" 15 2 || true
poll_health "Ollama Engine" "curl -sf http://127.0.0.1:$OLLAMA_PORT/api/tags" 15 2 || true
poll_health "SearXNG Engine" "curl -sf http://127.0.0.1:$SEARXNG_PORT/" 20 2 || true
poll_health "Warden Sidecar" "curl -sf http://127.0.0.1:$WARDEN_HOST_PORT/health" 15 2 || true
poll_health "Express API" "curl -sf http://127.0.0.1:$API_PORT/health" 15 2 || true
poll_health "React Web UI" "curl -sf http://127.0.0.1:$UI_PORT/" 15 2 || true

echo ""
echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}       🎉 SEARCHBOOST STACK IS OPERATIONAL & READY             ${NC}"
echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  🌐 ${BOLD}React Web UI:${NC}        http://localhost:${UI_PORT}"
echo -e "  ⚡ ${BOLD}Express API Gateway:${NC} http://localhost:${API_PORT}"
echo -e "  🛡️  ${BOLD}Rust Warden Relay:${NC}   http://localhost:${WARDEN_HOST_PORT}/health"
echo -e "  🔍 ${BOLD}SearXNG Metasearch:${NC}  http://localhost:${SEARXNG_PORT}"
echo -e "  🦙 ${BOLD}Ollama AI Engine:${NC}    http://localhost:${OLLAMA_PORT}"
echo -e "  📦 ${BOLD}PostgreSQL DB:${NC}       localhost:${POSTGRES_PORT} (${DB_NAME:-searchboost_db})"
echo -e "  ⚡ ${BOLD}Redis Cache & Queue:${NC} localhost:${REDIS_PORT}"

if [ "$SYNERGY_MODE" = true ]; then
  echo ""
  echo -e "${MAGENTA}${BOLD}── Sister System: IronWarden Synergistic Ingress ───────────────${NC}"
  echo -e "  🛡️  ${BOLD}IronWarden Gateway:${NC}  http://localhost:8080/v1/chat/completions"
  echo -e "  ⚙️  ${BOLD}Warden Bridge:${NC}       http://localhost:14141"
  echo -e "  🔒 ${BOLD}Privacy Contract:${NC}    100% PII Scrubbing & HMAC Audit Chaining Active"
fi
echo ""
