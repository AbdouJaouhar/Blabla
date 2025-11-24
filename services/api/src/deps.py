from fastapi import Header, HTTPException
from sqlalchemy import select

from libs.auth.manager import AuthManager
from libs.db import AsyncSessionLocal
from libs.models import Users

auth = AuthManager()


async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Unauthorized")

    token = authorization.split(" ")[1]
    payload = auth.verify_token(token)
    if not payload:
        raise HTTPException(401, "Invalid token")

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Users).where(Users.id == int(payload["sub"])))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(401, "User not found")

        return user
