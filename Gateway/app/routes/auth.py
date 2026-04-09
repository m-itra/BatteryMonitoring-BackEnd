from app.models.auth import RegisterRequest, LoginRequest, LoginResponse
from app.utils.proxy_request import proxy_request
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Response
from app.config import *


router = APIRouter()

@router.post("/api/auth/register", tags=["Auth"])
async def register(data: RegisterRequest):
    """
    Регистрация нового пользователя
    """
    response = await proxy_request(
        f"{USER_SERVICE_URL}/register",
        "POST",
        headers={"Content-Type": "application/json"},
        body=data.model_dump_json().encode()
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.post("/api/auth/login", response_model=LoginResponse, tags=["Auth"])
async def login(data: LoginRequest):
    service_response = await proxy_request(
        f"{USER_SERVICE_URL}/login",
        "POST",
        headers={"Content-Type": "application/json"},
        body=data.model_dump_json().encode()
    )

    result = service_response.json()

    response = JSONResponse(
        content=result,
        status_code=service_response.status_code
    )

    if service_response.status_code == 200 and "access_token" in result:
        response.set_cookie(
            key="access_token",
            value=result["access_token"],
            httponly=True,
            secure=False, # В продакшене нужно True поспать
            samesite="lax",
            max_age=24 * 60 * 60  # 24 часа
        )

    return response