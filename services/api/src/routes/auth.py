from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select

from libs.auth.hashing import hash_password
from libs.auth.manager import AuthManager
from libs.db import AsyncSessionLocal
from libs.models import Users

router = APIRouter()
auth = AuthManager()


@router.post("/signin")
async def login(payload: dict):
    email = payload["email"]
    password = payload["password"]

    user = await auth.authenticate("password", email=email, password=password)
    if not user:
        raise HTTPException(401, "Invalid credentials")

    token = auth.create_token(user)
    return {"access_token": token}


@router.post("/signup")
async def signup(payload: dict):
    email = payload["email"]
    password = payload["password"]

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Users).where(Users.email == email))
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(400, "User already exists")

        user = Users(
            email=email,
            password_hash=hash_password(password),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = auth.create_token(user)
    return JSONResponse(content={"access_token": token})
