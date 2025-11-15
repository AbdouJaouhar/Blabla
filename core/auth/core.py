from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class Environment(str, Enum):
    LOCAL = "local"
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


class AuthBackendKind(str, Enum):
    JWT = "jwt"
    DUMMY = "dummy"


@dataclass
class User:
    id: str
    email: Optional[str] = None
    claims: dict[str, Any] = field(default_factory=dict)

    @property
    def is_authenticated(self) -> bool:
        return True


class AuthBackend(ABC):
    @abstractmethod
    async def authenticate(self, request) -> User | None: ...

    @abstractmethod
    async def get_user(self, request) -> User | None: ...
