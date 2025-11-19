import datetime
import enum
from typing import Any, Optional

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# -------------------------------------------------------------------
# Base
# -------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


# -------------------------------------------------------------------
# Enums
# -------------------------------------------------------------------
class SenderRole(enum.Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


# -------------------------------------------------------------------
# Users
# -------------------------------------------------------------------
class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    # SQLite safe JSON default
    user_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        server_default="{}",
        default=dict,
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    chats: Mapped[list["Chats"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    custom_model_prompts: Mapped[list["UserCustomModelPrompt"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


# -------------------------------------------------------------------
# Chats
# -------------------------------------------------------------------
class Chats(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        server_onupdate=func.now(),
    )

    user: Mapped["Users"] = relationship(back_populates="chats")

    messages: Mapped[list["Messages"]] = relationship(
        back_populates="chat",
        cascade="all, delete-orphan",
        order_by=lambda: Messages.created_at,
    )


# -------------------------------------------------------------------
# Messages
# -------------------------------------------------------------------
class Messages(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)

    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"), index=True
    )

    sender: Mapped[SenderRole] = mapped_column(
        Enum(SenderRole, native_enum=False)  # portable enum storage
    )

    content: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    chat: Mapped["Chats"] = relationship(back_populates="messages")


# -------------------------------------------------------------------
# Models / LLM Profile
# -------------------------------------------------------------------
class Models(Base):
    __tablename__ = "models"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)

    params: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        server_default="{}",
        default=dict,
    )

    system_prompt: Mapped[str | None] = mapped_column(Text)
    temperature: Mapped[float] = mapped_column(default=0.7)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    custom_model_prompts: Mapped[list["UserCustomModelPrompt"]] = relationship(
        back_populates="model", cascade="all, delete-orphan"
    )


# -------------------------------------------------------------------
# User Custom Model Prompt
# -------------------------------------------------------------------
class UserCustomModelPrompt(Base):
    __tablename__ = "user_custom_model_prompt"

    __table_args__ = (UniqueConstraint("user_id", "model_id", name="uq_user_model"),)
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    model_id: Mapped[int] = mapped_column(
        ForeignKey("models.id", ondelete="CASCADE"), index=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["Users"] = relationship(back_populates="custom_model_prompts")
    model: Mapped["Models"] = relationship(back_populates="custom_model_prompts")
