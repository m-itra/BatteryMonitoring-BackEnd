from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.utils.token_processing import verify_jwt_token

bearer_security = HTTPBearer(auto_error=False)


async def get_current_user_id(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_security),
) -> str:
    token = credentials.credentials if credentials else request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = verify_jwt_token(token)
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    return user_id
