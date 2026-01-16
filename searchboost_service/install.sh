#!/bin/bash

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# --- 1. PRE-FLIGHT CHECKS ---
setup_directories() {
    echo -e "${YELLOW}Setting up project structure...${NC}"
    mkdir -p configs searchboost_src container_configs

    # Take ownership of container configs if they exist to prevent EACCES
    if [ -d "container_configs" ]; then
        sudo chown -R $(whoami):$(whoami) container_configs/
    fi
}

check_and_set_env() {
    # If .env doesn't exist, create it with defaults
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}No .env found. Generating defaults...${NC}"
        cat <<EOT >> .env
OLLAMA_PORT=11434
OLLAMA_MODEL=llama3.2
SEARXNG_PORT=8080
REDIS_PORT=6379
REDIS_PASSWORD=$(openssl rand -hex 12)
EOT
    fi
    # Export variables for use in this script
    export $(grep -v '^#' .env | xargs)
}

# --- 2. SERVICE ORCHESTRATION ---
check_service() {
    local NAME=$1
    local CMD=$2
    local EXPECTED=$3
    local RETRIES=15
    local COUNT=0

    echo -n "Checking $NAME..."
    while [ $COUNT -lt $RETRIES ]; do
        RESULT=$(eval "$CMD" 2>/dev/null)
        if echo "$RESULT" | grep -q "$EXPECTED"; then
            echo -e " [${GREEN}READY${NC}]"
            return 0
        fi
        echo -n "."
        sleep 2
        ((COUNT++))
    done

    echo -e " [${RED}FAILED${NC}]"
    exit 1
}

run_stack() {
    echo -e "${YELLOW}Launching Docker Stack...${NC}"
    docker compose up -d
    sleep 10
    # Use our function for specific health checks
    check_service "Redis" "docker exec sb_redis redis-cli -a $REDIS_PASSWORD ping" "PONG"
    check_service "Ollama" "curl -s http://localhost:$OLLAMA_PORT/api/tags" "models"
    check_service "SearXNG" "curl -s http://localhost:$SEARXNG_PORT/status" "version"
}

setup_ollama_model() {
    echo -e "${YELLOW}Ensuring model $OLLAMA_MODEL is available...${NC}"
    if docker exec sb_ollama ollama list | grep -q "$OLLAMA_MODEL"; then
        echo -e "${GREEN}Model is already present.${NC}"
    else
        docker exec sb_ollama ollama pull "$OLLAMA_MODEL"
    fi
}

# --- 3. PYTHON ENVIRONMENT ---
setup_python() {
    echo -e "${YELLOW}Preparing Python environment...${NC}"
    [ ! -d "venv" ] && python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    # Add 'redis' and 'pydantic-settings' to your requirements
    pip install ollama requests aiohttp pydantic pydantic-settings redis arq
}

scaffold_configs() {
    # Add Redis config scaffold
    if [ ! -f "configs/redis.json" ]; then
        echo "{\"host\": \"localhost\", \"port\": $REDIS_PORT, \"password\": \"$REDIS_PASSWORD\"}" > configs/redis.json
    fi
    # Ensure SearXNG Settings exist for the container mount
    if [ ! -f "configs/searxng_settings.yml" ]; then
        cat <<EOT >> configs/searxng_settings.yml
use_default_settings: true
server:
  secret_key: "$(openssl rand -hex 16)"
  limiter: false
search:
  formats:
    - html
    - json
EOT
    fi
}

# --- MAIN EXECUTION ---
clear
echo -e "${GREEN}SearchBoost Orchestrator${NC}"
setup_directories
check_and_set_env
scaffold_configs
run_stack
setup_ollama_model
setup_python

echo -e "\n${GREEN}Success: Infrastructure is synchronized and healthy.${NC}"
