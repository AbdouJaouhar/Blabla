from sqlalchemy import select

from libs.db import AsyncSessionLocal
from libs.models import Chats, Messages, SenderRole


class ChatService:
    async def get_or_create_chat(self, user_id: int = 1):
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Chats).where(Chats.user_id == user_id, Chats.is_deleted == False)
            )
            chat = result.scalar_one_or_none()

            if not chat:
                chat = Chats(user_id=user_id, title=None)
                db.add(chat)
                await db.commit()
                await db.refresh(chat)

            return chat

    async def add_user_message(self, chat_id: int, content: str):
        async with AsyncSessionLocal() as db:
            msg = Messages(chat_id=chat_id, sender=SenderRole.user, content=content)
            db.add(msg)
            await db.commit()

    async def add_assistant_message(self, chat_id: int, content: str):
        async with AsyncSessionLocal() as db:
            msg = Messages(
                chat_id=chat_id, sender=SenderRole.assistant, content=content
            )
            db.add(msg)
            await db.commit()

    async def get_recent_messages(self, chat_id: int, window: int):
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Messages)
                .where(Messages.chat_id == chat_id, Messages.is_deleted == False)
                .order_by(Messages.created_at.desc())
                .limit(window)
            )
            msgs = list(result.scalars().all())
            msgs.reverse()
            return msgs
