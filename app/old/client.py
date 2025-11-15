import json
import os
from datetime import datetime

import uvicorn
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, Template
from openai import AsyncOpenAI

load_dotenv()

MODEL = os.getenv("CHAT_MODEL")
WINDOW_SIZE = int(os.getenv("WINDOW_SIZE", "4"))
SYSTEM_PROMPT_TEMPLATE = os.getenv("SYSTEM_PROMPT")

app = FastAPI()
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

router = APIRouter()


class ChatEngine:
    def __init__(self):
        self.summary = ""
        self.history = []

        self.client = AsyncOpenAI(
            api_key=os.getenv("API_KEY"),
            base_url=os.getenv("BASE_URL"),
        )

    async def summarize_history(self):
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

        resp = await self.client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": prompt}],
            stream=False,
        )

        return resp.choices[0].message.content.strip()

    async def generate(self, messages):
        assistant_reply = ""

        try:
            stream = await self.client.chat.completions.create(
                model=MODEL,
                messages=messages,
                stream=True,
            )

            async for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    assistant_reply += delta
                    yield f"data: {json.dumps({'token': delta})}\n\n"

            # Store assistant reply in persistent history
            self.history.append({"role": "assistant", "content": assistant_reply})

            await self.update_memory()

        except Exception as e:
            yield f"error: {json.dumps({'error': str(e)})}\n\n"

    async def handle_chat(self, user_msg: str):
        self.history.append({"role": "user", "content": user_msg})

        rendered_system_prompt = Template("{{prompt}}").render(
            prompt=SYSTEM_PROMPT_TEMPLATE,
            currentDateTime=datetime.now().isoformat(),
        )

        messages = [{"role": "system", "content": rendered_system_prompt}]

        dev_context = ""
        if self.summary:
            dev_context += f"### PERSISTENT MEMORY\n{self.summary}\n### END MEMORY\n\n"

        messages.append({"role": "assistant", "content": dev_context})

        for msg in self.history[-WINDOW_SIZE:]:
            messages.append(msg)

        return StreamingResponse(
            self.generate(messages),
            media_type="text/event-stream",
        )

    async def update_memory(self):
        if len(self.history) > WINDOW_SIZE:
            # Summarize BEFORE trimming
            self.summary = await self.summarize_history()
            # Keep only the last WINDOW_SIZE messages
            self.history = self.history[-WINDOW_SIZE:]


engine = ChatEngine()


@router.get("/", response_class=HTMLResponse)
def index():
    return env.get_template("index.html").render()


@router.post("/api/chat")
async def chat(request: Request):
    body = await request.json()
    user_msg = body.get("message", "")
    return await engine.handle_chat(user_msg)


app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("chat.client:app", host="0.0.0.0", port=3000, reload=True)
