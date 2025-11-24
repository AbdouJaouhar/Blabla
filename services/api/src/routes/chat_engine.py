import json
import os

import httpx
from dotenv import load_dotenv
from fastapi.responses import StreamingResponse

from services.api.src.routes.chat_service import ChatService

load_dotenv()

MODEL = os.getenv("CHAT_MODEL")
VLLM_URL = "http://localhost:8000/v1/chat/completions"
WINDOW_SIZE = int(os.getenv("WINDOW_SIZE", "4"))
SYSTEM_PROMPT_TEMPLATE = os.getenv("SYSTEM_PROMPT", "")
MODEL_TEMPERATURE = os.getenv("MODEL_TEMPERATURE")


class ChatEngine:
    def __init__(self):
        self.summary = ""
        self.chat_service = ChatService()

    async def load_history(self, chat_id):
        msgs = await self.chat_service.get_recent_messages(chat_id, WINDOW_SIZE)
        history = []
        for m in msgs:
            history.append({"role": m.sender.value, "content": m.content})
        return history

    async def summarize_history(self, history):
        dialog_text = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in history)

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
        print(resp)
        return resp["choices"][0]["message"]["content"].strip()

    async def handle_chat(self, user_msg, images):
        chat = await self.chat_service.get_or_create_chat()

        history = await self.load_history(chat.id)

        content = user_msg
        if images:
            content += "\n[User sent images: " + ", ".join(images) + "]"

        await self.chat_service.add_user_message(chat.id, content)

        history.append({"role": "user", "content": content})

        messages = []
        messages.append({"role": "system", "content": SYSTEM_PROMPT_TEMPLATE})

        if self.summary:
            messages.append(
                {"role": "system", "content": f"### MEMORY\n{self.summary}\n"}
            )

        window = history[-WINDOW_SIZE:]
        messages.extend(window)

        return StreamingResponse(
            self.stream_vllm(chat.id, messages),
            media_type="text/event-stream",
        )

    async def stream_vllm(self, chat_id, messages):
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

                if assistant_reply:
                    await self.chat_service.add_assistant_message(
                        chat_id, assistant_reply
                    )

                await self.update_memory(chat_id)

    async def update_memory(self, chat_id):
        history = await self.load_history(chat_id)
        if len(history) > WINDOW_SIZE:
            self.summary = await self.summarize_history(history)
