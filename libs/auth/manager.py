from libs.auth.backends.password import PasswordAuthBackend
from libs.auth.jwt import create_jwt, decode_jwt


class AuthManager:
    def __init__(self):
        self.backends = {"password": PasswordAuthBackend()}

    async def authenticate(self, provider: str, **kwargs):
        backend = self.backends.get(provider)
        if not backend:
            return None
        return await backend.authenticate(**kwargs)

    def create_token(self, user):
        return create_jwt(user.id)

    def verify_token(self, token):
        return decode_jwt(token)
