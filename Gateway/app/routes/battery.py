from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.models.battery import BatteryLogRequest, SubmitResponse
from app.utils.token_processing import verify_jwt_token
from app.utils.proxy_request import proxy_request
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Security
from app.config import *

router = APIRouter()
security = HTTPBearer()


@router.post("/api/battery/submit", response_model=SubmitResponse, tags=["Battery"])
async def submit_battery_log(
        data: BatteryLogRequest,
        credentials: HTTPAuthorizationCredentials = Security(security)
):
    # Извлекаем и проверяем JWT
    token = credentials.credentials
    payload = verify_jwt_token(token)
    user_id = payload.get("user_id")

    # Отправляем данные в ProcessingService
    response = await proxy_request(
        f"{PROCESSING_SERVICE_URL}/submit",
        "POST",
        headers={
            "Content-Type": "application/json",
            "X-User-Id": user_id
        },
        body=data.model_dump_json().encode()
    )

    # Возвращаем ответ клиенту (включая device_id, если он сгенерирован)
    return JSONResponse(content=response.json(), status_code=response.status_code)
