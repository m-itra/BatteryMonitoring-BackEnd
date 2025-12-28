from fastapi import HTTPException, APIRouter, Header
from app.db.connection import get_db_connection
from app.db.cycle import create_fake_cycle
from app.db.device import get_device_by_id
from app.db.device import create_device
from app.models.battery import SubmitResponse, BatteryLogRequest

import uuid

router = APIRouter()


@router.post("/submit", response_model=SubmitResponse)
def submit_battery_log(data: BatteryLogRequest,
                       x_user_id: str = Header(..., description="User ID from Gateway")):
    try:
        with get_db_connection() as conn:

            if data.device_id:
                device = get_device_by_id(conn, data.device_id)

                if not device:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Устройство с device_id '{data.device_id}' не найдено"
                    )

                if device['user_id'] != x_user_id:
                    raise HTTPException(
                        status_code=403,
                        detail="Устройство принадлежит другому пользователю"
                    )

            else:
                data.device_id = str(uuid.uuid4())
                create_device(conn, data.device_id, data.device_name, x_user_id)

            create_fake_cycle(conn, data.device_id, x_user_id)
            cycle_created = True

            conn.commit()

            return SubmitResponse(
                status="success",
                device_id=data.device_id,
                cycle_created=cycle_created
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
