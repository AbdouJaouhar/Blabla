# 🌳 Blabla

Run LLMs locally with a web interface (based on NextJS). Chat with models like Qwen or Phi using your own GPU.

## What's included

- **Frontend**: Next.js chat UI with markdown, LaTeX, and Mermaid diagram support
- **Backend**: FastAPI service with user authentication
- **Model Server**: vLLM for fast inference with KV caching via Redis
- **Database**: SQLAlchemy + Alembic for user/chat persistence

## Project vision

Right now, this is a standard chat interface. The goal is to evolve it into something more flexible a graph-based discussion system where conversations branch out instead of staying linear. Think treelike exploration of ideas where you can fork discussions, explore different paths, and see how concepts connect.

The aim is to support tree-based thinking, branching reasoning that lets you map out complex thoughts visually and navigate between different exploration threads.

## Requirements

- Python 3.10+
- Node.js 18+
- CUDA-compatible GPU
- Redis (auto-installed by start script)

## Quick Start

1. Copy the example config:
```bash
cp env.example.txt .env
```

2. Edit `.env` to set your model:
```bash
CHAT_MODEL=Qwen/Qwen2.5-7B-Instruct-AWQ
MAX_MODEL_LEN=8192
GPU_MEMORY_UTILIZATION=0.75
```

3. Run everything:
```bash
bash scripts/start.sh
```

This starts Redis, vLLM, the API server, and the frontend. Access the UI at http://localhost:3000.

## Running specific services

```bash
# Just the model server
bash scripts/start.sh --service vllm

# Just the backend
bash scripts/start.sh --service backend

# Just the frontend
bash scripts/start.sh --service frontend
```

## Database setup

```bash
# Initialize database
bash scripts/init.sh

# Run migrations
bash scripts/migrate.sh
```

## Project structure

```
├── frontend/          # Next.js app
├── services/api/      # FastAPI backend
├── libs/              # Shared code (models, auth, db)
├── scripts/           # Helper scripts
└── alembic/           # Database migrations
```

## Tech stack

**Frontend**: Next.js, TypeScript, TailwindCSS, React Markdown  
**Backend**: FastAPI, SQLAlchemy, python-jose  
**Inference**: vLLM, PyTorch, Transformers  
**Caching**: Redis (LMCache for KV)  
**Package management**: UV (Python), npm (Node)

## Logs

All services log to `logs/` with ANSI colors stripped for compatibility with `lnav`:

```bash
lnav logs/
```

## Notes

- First startup downloads the model (several GB)
- Adjust `GPU_MEMORY_UTILIZATION` in `.env` if you run out of VRAM
- The system prompt in `.env` controls model behavior (text vs diagrams)
