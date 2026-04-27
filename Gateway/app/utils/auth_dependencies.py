from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.utils.token_processing import verify_jwt_token

bearer_security = HTTPBearer(auto_error=False)


async def get_current_user_payload(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_security),
) -> dict:
    token = credentials.credentials if credentials else request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = verify_jwt_token(token)
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    return payload


async def get_current_user_id(
    payload: dict = Depends(get_current_user_payload),
) -> str:
    return payload["user_id"]


async def require_admin(
    payload: dict = Depends(get_current_user_payload),
) -> dict:
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return payload
