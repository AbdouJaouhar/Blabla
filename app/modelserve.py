import os
import subprocess

from dotenv import load_dotenv

load_dotenv()

CHAT_MODEL = os.getenv("CHAT_MODEL")
MAX_MODEL_LEN = os.getenv("MAX_MODEL_LEN")
GPU_MEMORY_UTILIZATION = os.getenv("GPU_MEMORY_UTILIZATION")
SWAP_SPACE = os.getenv("SWAP_SPACE")

cmd = [
    "vllm",
    "serve",
    CHAT_MODEL,
    "--max-model-len",
    MAX_MODEL_LEN,
    "--gpu-memory-utilization",
    GPU_MEMORY_UTILIZATION,
    "--swap-space",
    SWAP_SPACE,
    "--port",
    "8000",
    "--host",
    "0.0.0.0",
]

print("Starting vLLM server...")
print(" ".join(cmd))

subprocess.run(cmd)
