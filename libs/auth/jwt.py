import datetime

import jwt

SECRET = "CHANGE_THIS"
ALGO = "HS256"


def create_jwt(user_id: int):
    payload = {
        "sub": str(user_id),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
    }
    return jwt.encode(payload, SECRET, algorithm=ALGO)


def decode_jwt(token: str):
    try:
        return jwt.decode(token, SECRET, algorithms=[ALGO])
    except Exception:
        return None
