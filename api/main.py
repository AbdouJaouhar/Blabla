import copy
import json
import os

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

load_dotenv()

MODEL = os.getenv("CHAT_MODEL")
VLLM_URL = "http://localhost:8000/v1/chat/completions"
WINDOW_SIZE = int(os.getenv("WINDOW_SIZE", "4"))
SYSTEM_PROMPT_TEMPLATE = os.getenv("SYSTEM_PROMPT", "")
MODEL_TEMPERATURE = os.getenv("MODEL_TEMPERATURE")

app = FastAPI()


@app.options("/api/chat")
async def options_handler():
    return {}


# Enable CORS for the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatEngine:
    def __init__(self):
        self.summary = ""
        self.history = []

    async def summarize_history(self):
        """Use vLLM itself to summarize memory."""
        dialog_text = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in self.history
        )

        user_prompt = (
            "Update the persistent conversation summary.\n\n"
            "Rules:\n"
            "- Keep user facts, preferences, goals.\n"
            "- Remove chit-chat.\n"
            "- Keep it short, accurate, factual.\n"
            "- Never contradict previous summary.\n\n"
            f"PREVIOUS SUMMARY:\n{self.summary or '(empty)'}\n\n"
            f"NEW DIALOG:\n{dialog_text}\n\n"
            "UPDATED SUMMARY:"
        )

        async with httpx.AsyncClient(timeout=None) as client:
            r = await client.post(
                VLLM_URL,
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a memory engine."},
                        {"role": "user", "content": user_prompt},
                    ],
                    "stream": False,
                    "temperature": MODEL_TEMPERATURE,
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

                    payload = line.removeprefix("data:").strip()

                    if payload == "[DONE]":
                        break

                    token_data = json.loads(payload)
                    delta_obj = token_data["choices"][0].get("delta", {}) or {}
                    delta = delta_obj.get("content", "")

                    if delta:
                        assistant_reply += delta
                        yield f"data: {json.dumps({'token': delta})}\n\n"

                # Store assistant message (role="assistant")
                if assistant_reply:
                    self.history.append(
                        {"role": "assistant", "content": assistant_reply}
                    )

                await self.update_memory()

    async def handle_chat(self, user_msg: str, images: list[str]):
        images = images or []

        # For memory: text-only representation
        history_text = user_msg or ""
        if images:
            history_text += "\n[User sent images: " + ", ".join(images) + "]"

        self.history.append({"role": "user", "content": history_text})

        # Render system prompt WITHOUT Jinja
        rendered_system_prompt = SYSTEM_PROMPT_TEMPLATE

        messages = [{"role": "system", "content": rendered_system_prompt}]

        # Add memory
        if self.summary:
            messages.append(
                {"role": "system", "content": f"### MEMORY\n{self.summary}\n"}
            )

        # Add recent conversation window (deep copy so we can mutate safely)
        window = self.history[-WINDOW_SIZE:]
        messages.extend(copy.deepcopy(window))

        # Replace last user message in this window with multimodal content
        if messages and messages[-1]["role"] == "user":
            if images:
                user_content = []
                if user_msg:
                    user_content.append({"type": "text", "text": user_msg})

                # Convert relative URLs like "/uploads/..." to absolute
                for rel_url in images:
                    url = rel_url
                    if rel_url.startswith("/"):
                        url = f"http://localhost:3000{rel_url}"

                    user_content.append(
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": url,
                            },
                        }
                    )

                messages[-1] = {
                    "role": "user",
                    "content": user_content,
                }
            else:
                # pure text user message; nothing special
                messages[-1] = {
                    "role": "user",
                    "content": user_msg,
                }

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
    user_msg = body.get("message", "") or ""
    images = body.get("images", []) or []
    return await engine.handle_chat(user_msg, images)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=3000, reload=True)
