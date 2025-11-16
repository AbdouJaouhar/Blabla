# Blabla

## Start Chat service

uv pip install vllm --torch-backend=auto

```
uv run chat/server.py
uv run uvicorn chat.client:app --host 0.0.0.0 --port 3000
```


nano ~/.tmux.conf
set -g mouse on
tmux source-file ~/.tmux.conf
