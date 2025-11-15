from __future__ import annotations

from core import AuthBackend, User
from jose import ExpiredSignatureError, JWTError, jwt
from jose.exceptions import JWTClaimsError


class JWTBearerAuth(AuthBackend):
    def __init__(self, *, public_key: str, issuer: str, audience: str):
        self.public_key = public_key
        self.issuer = issuer
        self.audience = audience

    async def authenticate(self, request):
        header = request.headers.get("Authorization")
        if not header:
            return None

        if not header.startswith("Bearer "):
            return None

        token = header.split(" ", 1)[1]

        try:
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=["RS256"],
                issuer=self.issuer,
                audience=self.audience,
                options={
                    "verify_signature": True,
                    "verify_aud": True,
                    "verify_iss": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                },
            )

        except ExpiredSignatureError:
            return None
        except JWTClaimsError:
            return None
        except JWTError:
            return None

        return self._user_from_payload(payload)

    async def get_user(self, request):
        return await self.authenticate(request)

    def _user_from_payload(self, payload: dict) -> User:
        sub = payload.get("sub")
        if not isinstance(sub, str):
            raise JWTClaimsError("Missing or invalid 'sub' claim")

        return User(
            id=sub,
            email=payload.get("email"),
            claims=payload,
        )
