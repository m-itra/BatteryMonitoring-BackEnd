import uuid

from fastapi import APIRouter, Header, HTTPException

from app.db.connection import get_db_session
from app.db.device import create_device, get_device_record_by_id
from app.models.battery import (
    BatteryLogBatchRequest,
    BatteryLogBatchResponse,
)
from app.services.battery_batch import process_battery_batch
from app.utils.grpc_user_client import validate_user_via_grpc

router = APIRouter()


@router.post("/logs/batch", response_model=BatteryLogBatchResponse)
async def submit_battery_logs_batch(
    data: BatteryLogBatchRequest,
    x_user_id: str = Header(..., description="User ID from Gateway"),
):
    try:
        user_validation = await validate_user_via_grpc(x_user_id)

        if not user_validation["exists"]:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID '{x_user_id}' not found",
            )

        async with get_db_session() as session:
            try:
                if data.device_id:
                    device = await get_device_record_by_id(session, data.device_id, for_update=True)

                    if device is None:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Device with device_id '{data.device_id}' not found",
                        )

                    if str(device.user_id) != x_user_id:
                        raise HTTPException(
                            status_code=403,
                            detail="Device belongs to another user",
                        )
                else:
                    if data.device_name is None:
                        raise HTTPException(
                            status_code=400,
                            detail="device_name is required when device_id is not provided",
                        )

                    generated_device_id = str(uuid.uuid4())
                    device = await create_device(
                        session,
                        generated_device_id,
                        data.device_name,
                        x_user_id,
                        battery_id=data.battery_id,
                        reference_capacity_mwh=data.reference_capacity_mwh,
                    )

                ingest_result = await process_battery_batch(
                    session,
                    device=device,
                    request_data=data,
                )
                await session.commit()

                return BatteryLogBatchResponse(
                    status="success",
                    message="Battery batch processed",
                    device_id=ingest_result.device_id,
                    processed_samples=ingest_result.processed_samples,
                    duplicate_samples=ingest_result.duplicate_samples,
                    completed_sessions=ingest_result.completed_sessions,
                    completed_cycles=ingest_result.completed_cycles,
                )
            except HTTPException:
                await session.rollback()
                raise
            except Exception:
                await session.rollback()
                raise

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
