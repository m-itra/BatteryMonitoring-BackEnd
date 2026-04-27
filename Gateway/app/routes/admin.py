from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.config import ANALYTICS_SERVICE_URL, USER_SERVICE_URL
from app.models.auth import AdminStatsResponse, AdminUsersResponse, DeleteUserResponse
from app.utils.auth_dependencies import require_admin
from app.utils.proxy_request import proxy_request

router = APIRouter()


@router.get("/api/admin/users", response_model=AdminUsersResponse, tags=["Admin"])
async def get_admin_users(_admin_payload: dict = Depends(require_admin)):
    response = await proxy_request(
        f"{USER_SERVICE_URL}/admin/users",
        "GET",
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.get("/api/admin/stats", response_model=AdminStatsResponse, tags=["Admin"])
async def get_admin_stats(_admin_payload: dict = Depends(require_admin)):
    user_response = await proxy_request(f"{USER_SERVICE_URL}/admin/stats", "GET")
    if user_response.status_code != 200:
        return JSONResponse(content=user_response.json(), status_code=user_response.status_code)

    battery_response = await proxy_request(f"{ANALYTICS_SERVICE_URL}/admin/stats", "GET")
    if battery_response.status_code != 200:
        return JSONResponse(content=battery_response.json(), status_code=battery_response.status_code)

    merged = {
        **user_response.json(),
        **battery_response.json(),
    }
    return JSONResponse(content=merged, status_code=200)


@router.delete("/api/admin/users/{user_id}", response_model=DeleteUserResponse, tags=["Admin"])
async def delete_admin_user(user_id: str, _admin_payload: dict = Depends(require_admin)):
    response = await proxy_request(
        f"{USER_SERVICE_URL}/admin/users/{user_id}",
        "DELETE",
    )
    return JSONResponse(content=response.json(), status_code=response.status_code)
