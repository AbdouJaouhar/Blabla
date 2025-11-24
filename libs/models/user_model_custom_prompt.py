from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class UserModelCustomPrompt(Base):
    __tablename__ = "user_model_custom_prompt"

    id: Mapped[int] = mapped_column(primary_key=True)

    model_id: Mapped[int] = mapped_column(
        ForeignKey("models.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    prompt: Mapped[str | None] = mapped_column(Text)

    user: Mapped["Users"] = relationship(back_populates="custom_model_prompts")
    model: Mapped["Models"] = relationship(back_populates="custom_model_prompts")

    __table_args__ = (UniqueConstraint("user_id", "model_id", name="uq_user_model"),)
