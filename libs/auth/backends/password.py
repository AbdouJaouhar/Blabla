from sqlalchemy import select

from libs.auth.base import AuthBackend
from libs.auth.hashing import verify_password
from libs.db import AsyncSessionLocal
from libs.models import Users


class PasswordAuthBackend(AuthBackend):
    async def authenticate(self, email: str, password: str):
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Users).where(Users.email == email))
            user = result.scalar_one_or_none()

            if not user:
                return None

            if not verify_password(password, user.password_hash):
                return None

            return user
