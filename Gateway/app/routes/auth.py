from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.config import (
    AUTH_COOKIE_MAX_AGE_SECONDS,
    AUTH_COOKIE_SAMESITE,
    AUTH_COOKIE_SECURE,
    USER_SERVICE_URL,
)
from app.models.auth import DeleteUserResponse, LoginRequest, LoginResponse, RegisterRequest
from app.utils.auth_dependencies import get_current_user_id
from app.utils.proxy_request import proxy_request

router = APIRouter()


@router.post("/api/auth/register", tags=["Auth"])
async def register(data: RegisterRequest):
    response = await proxy_request(
        f"{USER_SERVICE_URL}/register",
        "POST",
        headers={"Content-Type": "application/json"},
        body=data.model_dump_json().encode(),
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.post("/api/auth/login", response_model=LoginResponse, tags=["Auth"])
async def login(data: LoginRequest):
    service_response = await proxy_request(
        f"{USER_SERVICE_URL}/login",
        "POST",
        headers={"Content-Type": "application/json"},
        body=data.model_dump_json().encode(),
    )

    result = service_response.json()
    response = JSONResponse(content=result, status_code=service_response.status_code)

    if service_response.status_code == 200 and "access_token" in result:
        response.set_cookie(
            key="access_token",
            value=result["access_token"],
            httponly=True,
            secure=AUTH_COOKIE_SECURE,
            samesite=AUTH_COOKIE_SAMESITE,
            max_age=AUTH_COOKIE_MAX_AGE_SECONDS,
        )

    return response


@router.post("/api/auth/logout", tags=["Auth"])
async def logout():
    response = JSONResponse(content={"message": "Logged out"}, status_code=200)
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=AUTH_COOKIE_SECURE,
        samesite=AUTH_COOKIE_SAMESITE,
    )
    return response


@router.delete("/api/auth/me", response_model=DeleteUserResponse, tags=["Auth"])
async def delete_current_user(
    user_id: str = Depends(get_current_user_id),
):
    service_response = await proxy_request(
        f"{USER_SERVICE_URL}/users/me",
        "DELETE",
        headers={"X-User-Id": user_id},
    )

    response = JSONResponse(content=service_response.json(), status_code=service_response.status_code)
    if service_response.status_code == 200:
        response.delete_cookie(
            key="access_token",
            httponly=True,
            secure=AUTH_COOKIE_SECURE,
            samesite=AUTH_COOKIE_SAMESITE,
        )
    return response
