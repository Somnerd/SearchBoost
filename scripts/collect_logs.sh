#!/bin/sh

# Use POSIX-compliant way to get script directory
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="$SCRIPT_DIR/../logs/test_logs/$TIMESTAMP"

mkdir -p "$LOG_DIR"

echo "🚀 Starting log collection for SearchBoost services..."
echo "📅 Timestamp: $TIMESTAMP"

# List of containers (POSIX-friendly space-separated string)
# Note: updated sb_worker to searchboost-worker-1 to match actual deployment
CONTAINERS="searchboost-worker-1 sb_warden sb_db sb_redis sb-searxng sb_ollama sb_api sb_ui"

for container in $CONTAINERS; do
    if docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
        echo "📥 Collecting logs for $container..."
        docker logs "$container" > "$LOG_DIR/${container}.log" 2>&1
    else
        echo "⚠️  Container $container not found, skipping..."
    fi
done

echo "✅ Log collection complete. Files available in $LOG_DIR"
ls -lh "$LOG_DIR"
