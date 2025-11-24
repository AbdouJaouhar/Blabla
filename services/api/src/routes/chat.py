from fastapi import APIRouter, Depends, Request
from libs.db import AsyncSessionLocal
from libs.models import Chats
from sqlalchemy import select

from ..deps import get_current_user
from .chat_engine import ChatEngine

router = APIRouter()
engine = ChatEngine()


@router.options("/send")
async def options_handler(user=Depends(get_current_user)):
    return {}


@router.post("/send")
async def chat(request: Request, user=Depends(get_current_user)):
    body = await request.json()
    user_msg = body.get("message", "") or ""
    images = body.get("images", []) or []
    return await engine.handle_chat(user_msg, images)


@router.post("/all")
async def chats(user=Depends(get_current_user)):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Chats).where(Chats.user_id == user.id, Chats.is_deleted.is_(False))
        )
        chats = result.scalar_one_or_none()

        return chats
