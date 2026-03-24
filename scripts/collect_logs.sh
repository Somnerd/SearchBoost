#!/bin/bash
# SearchBoost: Log Collection Utility
# Captures logs from all service containers with timestamps for debugging.

# Get the directory where the script is located and point to ../logs
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_DIR="$SCRIPT_DIR/../logs/test_logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

echo "🚀 Starting log collection for SearchBoost services..."
echo "📅 Timestamp: $TIMESTAMP"

CONTAINERS=("sb_worker" "sb_warden" "sb_db" "sb_redis" "sb_searxng" "sb_ollama" "sb_api" "sb_ui")

for container in "${CONTAINERS[@]}"; do
    if docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
        echo "📥 Collecting logs for $container..."
        docker logs "$container" > "$LOG_DIR/${container}_${TIMESTAMP}.log" 2>&1
    else
        echo "⚠️  Container $container not found, skipping..."
    fi
done

echo "✅ Log collection complete. Files available in $LOG_DIR"
ls -lh "$LOG_DIR" | grep "$TIMESTAMP"
