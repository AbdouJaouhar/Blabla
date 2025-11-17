#!/bin/bash
set -e

#######################################
# Install Redis + lnav if missing
#######################################
echo "Checking dependencies..."

if ! command -v redis-server >/dev/null 2>&1; then
  echo "Redis not found. Installing Redis..."

  sudo apt-get update -y
  sudo apt-get install -y lsb-release curl gpg

  curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
  sudo chmod 644 /usr/share/keyrings/redis-archive-keyring.gpg

  echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" |
    sudo tee /etc/apt/sources.list.d/redis.list

  sudo apt-get update -y
  sudo apt-get install -y redis
fi

if ! command -v lnav >/dev/null 2>&1; then
  echo "lnav not found. Installing..."
  sudo apt-get update -y
  sudo apt-get install -y lnav
fi

#######################################
# Kill old processes
#######################################
echo "Killing existing processes..."
pkill -f "vllm serve" 2>/dev/null || true
pkill -f "uvicorn app.api.main" 2>/dev/null || true
pkill -f "node" 2>/dev/null || true
pkill -f "redis-server" 2>/dev/null || true
sleep 1

#######################################
# Clean logs directory & create logs
#######################################
echo "Cleaning logs directory..."
rm -rf logs
mkdir -p logs

# Pre-create log files
touch logs/logs_backend.txt
touch logs/logs_frontend.txt
touch logs/logs_redis.txt
touch logs/logs_vllm.txt

#######################################
# Load .env if exists
#######################################
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

#######################################
# Start Redis Server
#######################################
echo "Starting Redis server..."
redis-server > logs/logs_redis.txt 2>&1 &
REDIS_PID=$!
echo "Redis PID: $REDIS_PID"
sleep 0.5

#######################################
# Start Backend
#######################################
echo "Starting backend..."
uv run uvicorn app.api.main:app --host 0.0.0.0 --port 3001 --reload \
  > logs/logs_backend.txt 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

#######################################
# Start Frontend
#######################################
echo "Starting frontend..."
cd app/chat
npm run dev > ../logs/logs_frontend.txt 2>&1 &
FRONTEND_PID=$!
cd ../..
echo "Frontend PID: $FRONTEND_PID"

#######################################
# Start vLLM
#######################################
echo "Starting vLLM..."

export LMCACHE_CHUNK_SIZE=256
export LMCACHE_USE_EXPERIMENTAL=True
export LMCACHE_REMOTE_URL="redis://localhost:6379"
export LMCACHE_REMOTE_SERDE="naive"

vllm serve "$CHAT_MODEL" \
  --max-model-len "$MAX_MODEL_LEN" \
  --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION" \
  --swap-space "$SWAP_SPACE" \
  --port 8000 \
  --host 0.0.0.0 \
  --kv-transfer-config '{"kv_connector":"LMCacheConnectorV1", "kv_role":"kv_both"}' \
  > logs/logs_vllm.txt 2>&1 &

VLLM_PID=$!
echo "vLLM PID: $VLLM_PID"

#######################################
# Cleanup on exit
#######################################
cleanup() {
  echo "Shutting down everything..."
  kill $VLLM_PID     2>/dev/null || true
  kill $BACKEND_PID  2>/dev/null || true
  kill $FRONTEND_PID 2>/dev/null || true
  kill $REDIS_PID    2>/dev/null || true
}
trap cleanup EXIT

echo "----------------------------------------"
echo "Everything is running!"
echo "Backend    → http://localhost:3001"
echo "Frontend   → http://localhost:3000"
echo "vLLM API   → http://localhost:8000"
echo "Redis      → redis://localhost:6379"
echo "----------------------------------------"
echo "To view logs with color:  lnav logs/"
echo "----------------------------------------"

wait
