from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    LOCAL = "local"
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


class AuthBackendKind(str, Enum):
    JWT = "jwt"
    DUMMY = "dummy"


class User(BaseModel):
    name: str
    email: str
    refresh_token: str | None = None


class AuthBackend(ABC):
    @abstractmethod
    async def authenticate(self, request) -> User | None: ...

    @abstractmethod
    async def get_user(self, request) -> User | None: ...


class JWTAuth(AuthBackend):
    def __init__(self, *, public_key: SecretStr, issuer: str, audience: str):
        self._public_key = public_key
        self._issuer = issuer
        self._audience = audience

    async def authenticate(self, request) -> User | None: ...

    async def get_user(self, request) -> User | None: ...


class DummyAuth(AuthBackend):
    def __init__(self, settings: Settings):
        self._settings = settings

    async def authenticate(self, request) -> User | None:
        return User(name="Dummy", email="dummy@example.com")

    async def get_user(self, request) -> User | None:
        return User(name="Dummy", email="dummy@example.com")


class JWTSettings(BaseModel):
    public_key: SecretStr
    issuer: str
    audience: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False, frozen=True)

    environment: Environment = Environment.LOCAL
    auth_backend: AuthBackendKind = AuthBackendKind.JWT

    jwt: JWTSettings | None = None

    @classmethod
    def forbid_dummy_in_prod(cls, v: AuthBackendKind, info) -> AuthBackendKind:
        if (
            info.data.get("environment") is Environment.PROD
            and v is AuthBackendKind.DUMMY
        ):
            raise ValueError("Auth configuration is flawed")
        return v


def build_auth_backend(settings: Settings) -> AuthBackend:
    match settings.auth_backend:
        case AuthBackendKind.JWT:
            if settings.jwt is None:
                raise RuntimeError("JWT settings missing")
            return JWTAuth(
                public_key=settings.jwt.public_key,
                issuer=settings.jwt.issuer,
                audience=settings.jwt.audience,
            )
        case AuthBackendKind.DUMMY:
            return DummyAuth(settings)
        case _:
            raise RuntimeError(f"Unknown backend {settings.auth_backend!r}")
