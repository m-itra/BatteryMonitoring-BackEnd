import uuid

from fastapi import APIRouter, Header, HTTPException

from app.db.connection import get_db_connection
from app.db.cycle import create_fake_cycle
from app.db.device import create_device, get_device_by_id
from app.models.battery import BatteryLogRequest, SubmitResponse
from app.utils.grpc_user_client import validate_user_via_grpc

router = APIRouter()


@router.post("/submit", response_model=SubmitResponse)
async def submit_battery_log(
        data: BatteryLogRequest,
        x_user_id: str = Header(..., description="User ID from Gateway")
):
    try:
        user_validation = await validate_user_via_grpc(x_user_id)

        if not user_validation["exists"]:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID '{x_user_id}' not found"
            )

        print(f"User validated via gRPC: {user_validation['name']} ({x_user_id})")

        with get_db_connection() as conn:
            try:
                if data.device_id:
                    device = get_device_by_id(conn, data.device_id)

                    if not device:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Device with device_id '{data.device_id}' not found"
                        )

                    if device["user_id"] != x_user_id:
                        raise HTTPException(
                            status_code=403,
                            detail="Device belongs to another user"
                        )
                else:
                    data.device_id = str(uuid.uuid4())
                    create_device(conn, data.device_id, data.device_name, x_user_id)

                create_fake_cycle(conn, data.device_id, x_user_id)
                conn.commit()

                return SubmitResponse(
                    status="success",
                    message="Battery log processed",
                    device_id=data.device_id,
                    cycle_created=True
                )
            except Exception:
                conn.rollback()
                raise

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
