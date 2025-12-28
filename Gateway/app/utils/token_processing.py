from fastapi import HTTPException
from app.config import *

import jwt


def verify_jwt_token(token: str) -> dict:
    """ Проверка и декодирование JWT токена """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")