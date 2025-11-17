#!/bin/bash
set -e

echo "set -g mouse on" > ~/.tmux.conf

# Reload tmux config if inside a tmux session
if [ -n "$TMUX" ]; then
    tmux source-file ~/.tmux.conf
    echo "tmux configuration reloaded."
else
    echo "Not inside a tmux session. Start tmux to use the new config."
fi

#######################################
# Parse arguments
#######################################
SERVICE="all"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --service)
      SERVICE="$2"
      shift
      shift
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

echo "Selected service: $SERVICE"

#######################################
# Flags to track which services we started
#######################################
STARTED_REDIS=false
STARTED_BACKEND=false
STARTED_FRONTEND=false
STARTED_VLLM=false

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
# Clean logs directory & create logs
#######################################
echo "Cleaning logs directory..."
rm -rf logs
mkdir -p logs

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
# Start Redis server
#######################################
if [[ "$SERVICE" == "redis" || "$SERVICE" == "all" ]]; then
  echo "Starting Redis server..."
  redis-server 2>&1 | sed -u "s/\x1b\[[0-9;]*m//g" > logs/logs_redis.txt &
  REDIS_PID=$!
  STARTED_REDIS=true
  echo "Redis PID: $REDIS_PID"
  sleep 0.5
fi

#######################################
# Start Backend
#######################################
if [[ "$SERVICE" == "backend" || "$SERVICE" == "all" ]]; then
  echo "Starting backend..."
  echo "Model utilisé: $CHAT_MODEL"
  uv run uvicorn app.api.main:app --host 0.0.0.0 --port 3001 --reload \
    2>&1 | sed -u "s/\x1b\[[0-9;]*m//g" > logs/logs_backend.txt &
  BACKEND_PID=$!
  STARTED_BACKEND=true
  echo "Backend PID: $BACKEND_PID"
fi

#######################################
# Start Frontend
#######################################
if [[ "$SERVICE" == "frontend" || "$SERVICE" == "all" ]]; then
  echo "Starting frontend..."
  cd app/chat
  npm run init 2>&1 | sed -u "s/\x1b\[[0-9;]*m//g" > ../../logs/logs_frontend.txt &
  FRONTEND_PID=$!
  STARTED_FRONTEND=true
  cd ../..
  echo "Frontend PID: $FRONTEND_PID"
fi

#######################################
# Start vLLM
#######################################
if [[ "$SERVICE" == "vllm" || "$SERVICE" == "all" ]]; then
  echo "Starting vLLM..."
  # sudo apt-get update -y
  # sudo apt-get install -y cuda-12-2
  export LD_LIBRARY_PATH=/usr/local/cuda-12.2/lib64:$LD_LIBRARY_PATH

  export LMCACHE_CHUNK_SIZE=256
  export LMCACHE_USE_EXPERIMENTAL=True
  export LMCACHE_REMOTE_URL="redis://localhost:6379"
  export LMCACHE_REMOTE_SERDE="naive"
  # Remove any existing CUDA entries from PATH and LD_LIBRARY_PATH
  export PATH=$(echo $PATH | tr ':' '\n' | grep -v cuda | tr '\n' ':' | sed 's/:$//')
  export LD_LIBRARY_PATH=$(echo $LD_LIBRARY_PATH 2>/dev/null | tr ':' '\n' | grep -v cuda | tr '\n' ':' | sed 's/:$//')

  # Add only CUDA 12.2
  export PATH=/usr/local/cuda-12.2/bin:$PATH
  export LD_LIBRARY_PATH=/usr/local/cuda-12.2/lib64:$LD_LIBRARY_PATH

  # Optional: also set CUDA_HOME and CUDA_PATH for tools that look for these
  export CUDA_HOME=/usr/local/cuda-12.2
  export CUDA_PATH=/usr/local/cuda-12.2


  # uv pip uninstall vllm
  # uv pip install vllm --torch-backend=auto
echo "Model utilisé: $CHAT_MODEL"
uv run vllm serve "$CHAT_MODEL" \
    --max-model-len "$MAX_MODEL_LEN" \
    --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION" \
    --swap-space "$SWAP_SPACE" \
    --port 8000 \
    --host 0.0.0.0 \
    --kv-transfer-config '{"kv_connector":"LMCacheConnectorV1", "kv_role":"kv_both"}'
  VLLM_PID=$!
  STARTED_VLLM=true
  echo "vLLM PID: $VLLM_PID"
fi

#######################################
# Cleanup on exit
#######################################
cleanup() {
  echo "Shutting down services started by this script..."

  $STARTED_VLLM     && kill $VLLM_PID     2>/dev/null || true
  $STARTED_BACKEND  && kill $BACKEND_PID  2>/dev/null || true
  $STARTED_FRONTEND && kill $FRONTEND_PID 2>/dev/null || true
  $STARTED_REDIS    && kill $REDIS_PID    2>/dev/null || true
}

trap cleanup EXIT

echo "----------------------------------------"
echo "Everything is running!"
echo "Backend    → http://localhost:3001"
echo "Frontend   → http://localhost:3000"
echo "vLLM API   → http://localhost:8000"
echo "Redis      → redis://localhost:6379"
echo "----------------------------------------"
echo "Logs contain no ANSI colors → compatible with lnav"
echo "To view logs: lnav logs/"
echo "----------------------------------------"

wait
