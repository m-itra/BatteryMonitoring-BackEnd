from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.utils.token_processing import verify_jwt_token
from app.models.analytics import UpdateDeviceRequest
from app.utils.proxy_request import proxy_request
from fastapi import APIRouter, Query, Request, Security
from fastapi.responses import JSONResponse
from app.config import *

router = APIRouter()
security = HTTPBearer()


@router.get("/api/analytics/devices", tags=["Analytics"])
async def get_devices(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Security(security)
):
    """
    Получить
    список
    устройств(требует
    JWT)"""

    token = credentials.credentials
    payload = verify_jwt_token(token)
    user_id = payload.get("user_id")

    response = await proxy_request(
        f"{ANALYTICS_SERVICE_URL}/devices",
        "GET",
        headers={"X-User-Id": user_id}
    )

    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.get("/api/analytics/cycles", tags=["Analytics"])
async def get_cycles(
        request: Request,
        device_id: str = Query(..., min_length=1),
        limit: int = Query(default=50, ge=1, le=200),
        credentials: HTTPAuthorizationCredentials = Security(security)
):
    token = credentials.credentials
    payload = verify_jwt_token(token)
    user_id = payload["user_id"]

    response = await proxy_request(
        f"{ANALYTICS_SERVICE_URL}/cycles",
        "GET",
        headers={"X-User-Id": user_id},
        params={
            "device_id": device_id,
            "limit": limit,
        }
    )

    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.get("/api/analytics", tags=["Analytics"])
async def get_full_analytics(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Security(security)
):
    """
    Получить полную аналитику (требует JWT)
    """
    token = credentials.credentials
    payload = verify_jwt_token(token)
    user_id = payload["user_id"]

    response = await proxy_request(
        f"{ANALYTICS_SERVICE_URL}/analytics",
        "GET",
        headers={"X-User-Id": user_id}
    )

    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.put("/api/analytics/devices/{device_id}", tags=["Analytics"])
async def update_device(
        device_id: str,
        data: UpdateDeviceRequest,
        credentials: HTTPAuthorizationCredentials = Security(security)
):
    """
    Переименовать устройство(требует JWT)"""

    token = credentials.credentials
    payload = verify_jwt_token(token)
    user_id = payload.get("user_id")

    response = await proxy_request(
        f"{ANALYTICS_SERVICE_URL}/devices/{device_id}",
        "PUT",
        headers={
            "Content-Type": "application/json",
            "X-User-Id": user_id
        },
        body=data.model_dump_json().encode()
    )

    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.delete("/api/analytics/devices/{device_id}", tags=["Analytics"])
async def delete_device(
        device_id: str,
        request: Request,
        credentials: HTTPAuthorizationCredentials = Security(security)
):
    """
    Удалить
    устройство(требует
    JWT)"""

    token = credentials.credentials
    payload = verify_jwt_token(token)
    user_id = payload.get("user_id")

    response = await proxy_request(
        f"{ANALYTICS_SERVICE_URL}/devices/{device_id}",
        "DELETE",
        headers={"X-User-Id": user_id}
    )

    return JSONResponse(content=response.json(), status_code=response.status_code)
