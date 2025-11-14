import json
import os
from datetime import datetime

import uvicorn
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi_utils.cbv import cbv
from jinja2 import Environment, FileSystemLoader, Template
from openai import AsyncOpenAI

load_dotenv()

MODEL = os.getenv("CHAT_MODEL")
WINDOW_SIZE = int(os.getenv("WINDOW_SIZE", "4"))
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
env = Environment(loader=FileSystemLoader("templates"))

router = APIRouter()


@cbv(router)
class ChatEngine:
    def __init__(self):
        self.summary = ""
        self.history = []
        self.client = AsyncOpenAI(
            api_key=os.getenv("API_KEY"), base_url=os.getenv("BASE_URL")
        )

    async def summarize_history(self):
        prompt = (
            "You are an assistant that compresses long conversations.\n"
            "Summarize the following dialog into a concise factual memory,\n"
            "keeping important details, goals, personal preferences and context.\n\n"
            f"Previous summary:\n{self.summary}\n\n"
            f"Full dialog:\n{json.dumps(self.history)}\n\n"
            "Output only the improved updated summary."
        )

        resp = await self.client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            stream=False,
        )

        return resp.choices[0].message.content

    @router.get("/", response_class=HTMLResponse)
    def index(self):
        template = env.get_template("index.html")
        return template.render()

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

            self.history.append({"role": "assistant", "content": assistant_reply})
            await self._update_history()
        except Exception as e:
            yield f"error: {json.dumps({'error': str(e)})}\n\n"

    @router.post("/api/chat")
    async def chat(self, request: Request):
        body = await request.json()
        user_msg = body.get("message", "")

        self.history.append({"role": "user", "content": user_msg})

        rendered_prompt = Template(str(SYSTEM_PROMPT)).render(
            currentDateTime=datetime.now().isoformat()
        )

        messages = [{"role": "user", "content": rendered_prompt}]

        if self.summary:
            messages.append(
                {
                    "role": "assistant",
                    "content": "[MEMORY]\n" + self.summary,
                }
            )

        messages.extend(self.history[-WINDOW_SIZE:])

        return StreamingResponse(
            self.generate(messages), media_type="text/event-stream"
        )

    async def _update_history(self):
        if len(self.history) > WINDOW_SIZE:
            self.summary = await self.summarize_history()
            self.history = self.history[-WINDOW_SIZE:]


if __name__ == "__main__":
    app.include_router(router)
    uvicorn.run("server:app", host="0.0.0.0", port=3000, reload=True)
