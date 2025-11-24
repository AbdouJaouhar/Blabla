import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import SenderRole


class Messages(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"), index=True, nullable=False
    )

    sender: Mapped[SenderRole] = mapped_column(
        Enum(SenderRole, native_enum=True), nullable=False
    )

    content_preview: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    is_deleted: Mapped[bool] = mapped_column(default=False, index=True)

    chat: Mapped["Chats"] = relationship(back_populates="messages")


Index("ix_messages_chatid_created", Messages.chat_id, Messages.created_at)
