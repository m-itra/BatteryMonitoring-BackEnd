from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.config import PROCESSING_SERVICE_URL
from app.models.battery import (
    BatteryLogBatchRequest,
    BatteryLogBatchResponse,
)
from app.utils.auth_dependencies import get_current_user_id
from app.utils.proxy_request import proxy_request

router = APIRouter()


@router.post("/api/battery/logs/batch", response_model=BatteryLogBatchResponse, tags=["Battery"])
async def submit_battery_log_batch(
    data: BatteryLogBatchRequest,
    user_id: str = Depends(get_current_user_id),
):
    response = await proxy_request(
        f"{PROCESSING_SERVICE_URL}/logs/batch",
        "POST",
        headers={
            "Content-Type": "application/json",
            "X-User-Id": user_id,
        },
        body=data.model_dump_json().encode(),
    )

    return JSONResponse(content=response.json(), status_code=response.status_code)
