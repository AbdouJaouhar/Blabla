import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .user_model_custom_prompt import UserModelCustomPrompt


class Models(Base):
    __tablename__ = "models"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    params: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, server_default=text("'{}'::jsonb")
    )

    system_prompt: Mapped[str | None] = mapped_column(Text)
    temperature: Mapped[float] = mapped_column(default=0.7)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        server_onupdate=func.now(),
    )

    custom_model_prompts: Mapped[list["UserModelCustomPrompt"]] = relationship(
        back_populates="model",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
