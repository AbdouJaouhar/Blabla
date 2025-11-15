from __future__ import annotations

from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from .base import AuthBackend, AuthBackendKind, Environment
from .jwt import JWTAuth


class JWTSettings(BaseModel):
    public_key: SecretStr | None = None  # kept for backward compat (not used)
    jwks_url: str
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
                jwks_url=settings.jwt.jwks_url,
                issuer=settings.jwt.issuer,
                audience=settings.jwt.audience,
            )
        case AuthBackendKind.DUMMY:
            return DummyAuth(settings)
        case _:
            raise RuntimeError(f"Unknown backend {settings.auth_backend!r}")
