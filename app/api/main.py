import json
import os
from datetime import datetime

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from jinja2 import Template

load_dotenv()

MODEL = os.getenv("CHAT_MODEL")
VLLM_URL = "http://localhost:8000/v1/chat/completions"
WINDOW_SIZE = int(os.getenv("WINDOW_SIZE", "4"))
SYSTEM_PROMPT_TEMPLATE = os.getenv("SYSTEM_PROMPT")
app = FastAPI()


@app.options("/api/chat")
async def options_handler():
    return {}


# Enable CORS for the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # autorise TOUTES les origines
    allow_credentials=True,
    allow_methods=["*"],  # autorise GET, POST, OPTIONS, etc.
    allow_headers=["*"],  # autorise Content-Type, Authorization, etc.
)


class ChatEngine:
    def __init__(self):
        self.summary = ""
        self.history = []

    async def summarize_history(self):
        """Use vLLM itself to summarize memory."""
        prompt = (
            "You are a memory engine.\n"
            "Update the persistent conversation summary.\n\n"
            "Rules:\n"
            "- Keep user facts, preferences, goals.\n"
            "- Remove chit-chat.\n"
            "- Keep it short, accurate, factual.\n"
            "- Never contradict previous summary.\n\n"
            f"PREVIOUS SUMMARY:\n{self.summary}\n\n"
            f"NEW DIALOG:\n{json.dumps(self.history)}\n\n"
            "UPDATED SUMMARY:"
        )

        async with httpx.AsyncClient(timeout=None) as client:
            r = await client.post(
                VLLM_URL,
                json={
                    "model": MODEL,
                    "messages": [{"role": "system", "content": prompt}],
                    "stream": False,
                },
            )

        resp = r.json()
        return resp["choices"][0]["message"]["content"].strip()

    async def stream_vllm(self, messages):
        """Proxy streaming from vLLM to the client."""
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                VLLM_URL,
                json={"model": MODEL, "messages": messages, "stream": True},
            ) as r:
                assistant_reply = ""

                async for line in r.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue

                    payload = line.replace("data:", "").strip()

                    if payload == "[DONE]":
                        break

                    token_data = json.loads(payload)
                    delta = token_data["choices"][0]["delta"].get("content", "")

                    if delta:
                        assistant_reply += delta
                        yield f"data: {json.dumps({'token': delta})}\n\n"

                # Store assistant message in memory
                self.history.append({"role": "assistant", "content": assistant_reply})

                await self.update_memory()

    async def handle_chat(self, user_msg: str):
        self.history.append({"role": "user", "content": user_msg})

        rendered_system_prompt = Template("{{prompt}}").render(
            prompt=SYSTEM_PROMPT_TEMPLATE,
            currentDateTime=datetime.now().isoformat(),
        )

        messages = [{"role": "system", "content": rendered_system_prompt}]

        if self.summary:
            messages.append(
                {"role": "assistant", "content": f"### MEMORY\n{self.summary}\n"}
            )

        messages.extend(self.history[-WINDOW_SIZE:])

        return StreamingResponse(
            self.stream_vllm(messages),
            media_type="text/event-stream",
        )

    async def update_memory(self):
        if len(self.history) > WINDOW_SIZE:
            self.summary = await self.summarize_history()
            self.history = self.history[-WINDOW_SIZE:]


engine = ChatEngine()


@app.post("/api/chat")
async def chat(request: Request):
    body = await request.json()
    user_msg = body.get("message", "")
    return await engine.handle_chat(user_msg)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=3000, reload=True)
