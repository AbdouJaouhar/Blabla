# pydantic_models.py

from __future__ import annotations

import datetime
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field

# ===================================================================
# ENUMS
# ===================================================================


class SenderRole(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


# ===================================================================
# BASE
# ===================================================================


class OrmBase(BaseModel):
    """Base class for all Pydantic schemas, enables ORM mode"""

    model_config = ConfigDict(from_attributes=True)


# ===================================================================
# USER MODELS
# ===================================================================


class UserCreate(OrmBase):
    email: str
    password: str  # Plain password input only


class UserUpdate(OrmBase):
    email: Optional[str] = None
    user_metadata: Optional[dict[str, Any]] = None


class UserRead(OrmBase):
    id: int
    email: str
    user_metadata: dict[str, Any]
    created_at: datetime.datetime


class UserReadWithChats(UserRead):
    chats: List["ChatRead"]


class UserReadWithCustomPrompts(UserRead):
    custom_model_prompts: List["UserCustomModelPromptRead"]


# ===================================================================
# CHAT MODELS
# ===================================================================


class ChatCreate(OrmBase):
    user_id: int
    title: Optional[str] = None


class ChatUpdate(OrmBase):
    title: Optional[str] = None
    summary: Optional[str] = None


class ChatRead(OrmBase):
    id: int
    user_id: int
    title: Optional[str]
    summary: Optional[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime


class ChatReadWithMessages(ChatRead):
    messages: List["MessageRead"]


# ===================================================================
# MESSAGE MODELS
# ===================================================================


class MessageCreate(OrmBase):
    chat_id: int
    sender: SenderRole
    content: str


class MessageRead(OrmBase):
    id: int
    chat_id: int
    sender: SenderRole
    content: str
    created_at: datetime.datetime


# ===================================================================
# MODEL (LLM PROFILE) MODELS
# ===================================================================


class ModelCreate(OrmBase):
    name: str
    params: dict[str, Any] = Field(default_factory=dict)
    system_prompt: Optional[str] = None
    temperature: float = 0.7


class ModelUpdate(OrmBase):
    params: Optional[dict[str, Any]] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None


class ModelRead(OrmBase):
    id: int
    name: str
    params: dict[str, Any]
    system_prompt: Optional[str]
    temperature: float
    created_at: datetime.datetime


class ModelReadWithPrompts(ModelRead):
    custom_model_prompts: List["UserCustomModelPromptRead"]


# ===================================================================
# USER CUSTOM MODEL PROMPT MODELS
# ===================================================================


class UserCustomModelPromptCreate(OrmBase):
    user_id: int
    model_id: int
    prompt: Optional[str] = None


class UserCustomModelPromptUpdate(OrmBase):
    prompt: Optional[str] = None


class UserCustomModelPromptRead(OrmBase):
    id: int
    user_id: int
    model_id: int
    prompt: Optional[str]


# ===================================================================
# FORWARD REF FIXES (REQUIRED)
# ===================================================================

UserReadWithChats.model_rebuild()
UserReadWithCustomPrompts.model_rebuild()
ChatReadWithMessages.model_rebuild()
ModelReadWithPrompts.model_rebuild()
