import uuid

from fastapi import APIRouter, Header, HTTPException

from app.db.connection import get_db_session
from app.db.cycle import DeviceNotFoundError, create_fake_cycle
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

        async with get_db_session() as session:
            try:
                if data.device_id:
                    device_id = data.device_id
                    device = await get_device_by_id(session, device_id)

                    if not device:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Device with device_id '{device_id}' not found"
                        )

                    if device["user_id"] != x_user_id:
                        raise HTTPException(
                            status_code=403,
                            detail="Device belongs to another user"
                        )
                else:
                    if data.device_name is None:
                        raise HTTPException(
                            status_code=400,
                            detail="device_name is required when device_id is not provided"
                        )

                    device_id = str(uuid.uuid4())
                    await create_device(session, device_id, data.device_name, x_user_id)

                await create_fake_cycle(session, device_id, x_user_id)
                await session.commit()

                return SubmitResponse(
                    status="success",
                    message="Battery log processed",
                    device_id=device_id,
                    cycle_created=True
                )
            except DeviceNotFoundError as e:
                await session.rollback()
                raise HTTPException(status_code=400, detail=str(e))
            except Exception:
                await session.rollback()
                raise

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
