import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .chat import Chats
from .user_model_custom_prompt import UserModelCustomPrompt


class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    user_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSON, server_default=text("'{}'::jsonb"), default=dict
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    )

    is_deleted: Mapped[bool] = mapped_column(default=False, index=True)

    chats: Mapped[list["Chats"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    custom_model_prompts: Mapped[list["UserModelCustomPrompt"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
