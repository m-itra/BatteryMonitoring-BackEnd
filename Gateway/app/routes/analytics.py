from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.config import ANALYTICS_SERVICE_URL
from app.models.analytics import UpdateDeviceRequest
from app.utils.auth_dependencies import get_current_user_id
from app.utils.proxy_request import proxy_request

router = APIRouter()


@router.get("/api/analytics/devices", tags=["Analytics"])
async def get_devices(user_id: str = Depends(get_current_user_id)):
    response = await proxy_request(
        f"{ANALYTICS_SERVICE_URL}/devices",
        "GET",
        headers={"X-User-Id": user_id},
    )

    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.get("/api/analytics/devices/{device_id}", tags=["Analytics"])
async def get_device_analytics(
    device_id: str,
    session_limit: int = Query(default=50, ge=1, le=200),
    cycle_limit: int = Query(default=50, ge=1, le=200),
    user_id: str = Depends(get_current_user_id),
):
    response = await proxy_request(
        f"{ANALYTICS_SERVICE_URL}/devices/{device_id}",
        "GET",
        headers={"X-User-Id": user_id},
        params={
            "session_limit": session_limit,
            "cycle_limit": cycle_limit,
        },
    )

    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.get("/api/analytics/cycles", tags=["Analytics"])
async def get_cycles(
    device_id: str = Query(..., min_length=1),
    limit: int = Query(default=50, ge=1, le=200),
    user_id: str = Depends(get_current_user_id),
):
    response = await proxy_request(
        f"{ANALYTICS_SERVICE_URL}/cycles",
        "GET",
        headers={"X-User-Id": user_id},
        params={
            "device_id": device_id,
            "limit": limit,
        },
    )

    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.get("/api/analytics", tags=["Analytics"])
async def get_full_analytics(user_id: str = Depends(get_current_user_id)):
    response = await proxy_request(
        f"{ANALYTICS_SERVICE_URL}/analytics",
        "GET",
        headers={"X-User-Id": user_id},
    )

    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.put("/api/analytics/devices/{device_id}", tags=["Analytics"])
async def update_device(
    device_id: str,
    data: UpdateDeviceRequest,
    user_id: str = Depends(get_current_user_id),
):
    response = await proxy_request(
        f"{ANALYTICS_SERVICE_URL}/devices/{device_id}",
        "PUT",
        headers={
            "Content-Type": "application/json",
            "X-User-Id": user_id,
        },
        body=data.model_dump_json().encode(),
    )

    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.delete("/api/analytics/devices/{device_id}", tags=["Analytics"])
async def delete_device(
    device_id: str,
    user_id: str = Depends(get_current_user_id),
):
    response = await proxy_request(
        f"{ANALYTICS_SERVICE_URL}/devices/{device_id}",
        "DELETE",
        headers={"X-User-Id": user_id},
    )

    return JSONResponse(content=response.json(), status_code=response.status_code)
