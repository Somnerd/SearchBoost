#!/bin/bash

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

setup_directories() {
    if [ ! -d "configs" ] || [ ! -d "searchboost_src" ]; then
        echo -e "${YELLOW}Creating directory structure...${NC}"
        mkdir -p configs searchboost_src
    else
        echo -e "${YELLOW}Directory structure already exists. Skipping creation...${NC}"
    fi
}

check_docker() {
    echo "Checking for Docker and Docker Compose..."
    if ! command -v docker &> /dev/null; then
        echo "Error: Docker is not installed. Please install it first."
        return 1
    fi
    echo "Docker is installed."

    if docker compose version &> /dev/null; then
        echo "Docker Compose (v2) is installed."
    elif command -v docker-compose &> /dev/null; then
        echo "Docker Compose (v1) is installed."
    else
        echo "Error: Docker Compose is not installed. Please install it first."
        return 1
    fi
}

check_and_set_ports() {
    OLLAMA_PORT=11434
    SEARXNG_PORT=8080

    EXISTING_OLLAMA_IMG=$(docker ps --format '{{.Names}} ({{.Ports}})' --filter "ancestor=ollama/ollama")
    EXISTING_SEARXNG_IMG=$(docker ps --format '{{.Names}} ({{.Ports}})' --filter "ancestor=searxng/searxng")

    if [ ! -z "$EXISTING_OLLAMA_IMG" ] || [ ! -z "$EXISTING_SEARXNG_IMG" ]; then
        echo -e "${YELLOW}Existing service instances detected:${NC}"
        [ ! -z "$EXISTING_OLLAMA_IMG" ] && echo -e "Ollama: $EXISTING_OLLAMA_IMG"
        [ ! -z "$EXISTING_SEARXNG_IMG" ] && echo -e "SearXNG: $EXISTING_SEARXNG_IMG"
        read -p "Install SearchBoost alongside these? (y/n): " DUPE_CHOICE
        if [[ ! "$DUPE_CHOICE" =~ ^[Yy]$ ]]; then
            return 0
        fi
    fi

    while lsof -Pi :$OLLAMA_PORT -sTCP:LISTEN -t >/dev/null ; do
        echo -e "${RED}Port $OLLAMA_PORT is in use.${NC}"
        read -p "Enter new port for Ollama: " OLLAMA_PORT
    done

    while lsof -Pi :$SEARXNG_PORT -sTCP:LISTEN -t >/dev/null ; do
        echo -e "${RED}Port $SEARXNG_PORT is in use.${NC}"
        read -p "Enter new port for SearXNG: " SEARXNG_PORT
    done

    echo "OLLAMA_PORT=$OLLAMA_PORT" > .env
    echo "SEARXNG_PORT=$SEARXNG_PORT" >> .env

    if [ -f "configs/local_ai.json" ]; then
        sed -i "s/\"port\": [0-9]*/\"port\": $OLLAMA_PORT/" configs/local_ai.json
    fi
    if [ -f "configs/web_search.json" ]; then
        sed -i "s/\"port\": [0-9]*/\"port\": $SEARXNG_PORT/" configs/web_search.json
    fi
}

run_docker_compose() {
    if [ "$(docker ps -q -f name=sb_ollama)" ] && [ "$(docker ps -q -f name=sb_searxng)" ]; then
        echo -e "${GREEN}Containers are already running.${NC}"
        return 0
    fi

    if [ "$(docker ps -aq -f name=sb_ollama)" ]; then
        echo -e "${YELLOW}Starting existing containers...${NC}"
        docker compose start
    else
        echo -e "${YELLOW}Deploying containers...${NC}"
        docker compose up -d
    fi

    if [ $? -ne 0 ]; then
        echo -e "${RED}Docker Compose failed.${NC}"
        return 1
    fi
}

setup_ollama_model() {
    echo -e "${YELLOW}Checking model status...${NC}"
    if docker exec sb_ollama ollama list | grep -q "llama3.2"; then
        echo -e "${GREEN}Llama 3.2 is already present.${NC}"
    else
        MAX_RETRIES=5
        RETRY_COUNT=0
        SUCCESS=false
        while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
            if docker exec sb_ollama ollama pull llama3.2; then
                SUCCESS=true
                break
            else
                RETRY_COUNT=$((RETRY_COUNT+1))
                sleep 5
            fi
        done
        if [ "$SUCCESS" = false ]; then
            return 1
        fi
    fi
}

verify_services_alive() {
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:${SEARXNG_PORT:-8080}/ | grep -qE "200|302"; then
        echo -e "${GREEN}SearXNG is alive.${NC}"
    else
        echo -e "${RED}SearXNG not responding.${NC}"
    fi

    if curl -s -o /dev/null -w "%{http_code}" http://localhost:${OLLAMA_PORT:-11434}/ | grep -q "200"; then
        echo -e "${GREEN}Ollama is alive.${NC}"
    else
        echo -e "${RED}Ollama not responding.${NC}"
    fi
}

setup_venv() {
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
}

install_dependencies() {
    pip install --upgrade pip
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        pip install ollama requests aiohttp openai argparse
    fi
}

scaffold_configs() {
    if [ ! -f "configs/local_ai.json" ]; then
        echo "{\"model\": \"llama3.2\", \"host\": \"localhost\", \"port\": 11434, \"stream\": false, \"role\":\"user\"}" > configs/local_ai.json
    fi
    if [ ! -f "configs/web_search.json" ]; then
        echo "{\"search_engine\": \"searxng\", \"num_results\": 5, \"host\": \"localhost\", \"port\": 8080}" > configs/web_search.json
    fi
}

setup_alias() {
    ALIAS_CMD="alias searchboost='$(pwd)/venv/bin/python $(pwd)/main.py'"
    if ! grep -q "alias searchboost=" ~/.bashrc; then
        echo -e "\n$ALIAS_CMD" >> ~/.bashrc
    fi
}

echo -e "${GREEN}SearchBoost Installation Started...${NC}"
setup_directories
check_docker
check_and_set_ports
run_docker_compose
sleep 5
setup_ollama_model
verify_services_alive
setup_venv
install_dependencies
scaffold_configs
setup_alias
echo -e "${GREEN}Installation complete.${NC}"