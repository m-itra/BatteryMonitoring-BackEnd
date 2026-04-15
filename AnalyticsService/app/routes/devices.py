from fastapi import APIRouter, Header, HTTPException
from sqlalchemy import delete, select

from app.db.connection import get_db_session
from app.db.models import Device
from app.db.query_helpers import device_summary_statement, parse_uuid_or_400
from app.models import DeviceInfo, UpdateDeviceRequest

router = APIRouter()


@router.get("/devices")
async def get_devices(x_user_id: str = Header(...)):
    user_id = parse_uuid_or_400(x_user_id, "X-User-Id")

    async with get_db_session() as session:
        result = await session.execute(device_summary_statement(user_id))
        devices = result.mappings().all()

        return {
            "devices": [
                DeviceInfo(
                    device_id=str(device["device_id"]),
                    device_name=device["device_name"],
                    created_at=device["created_at"],
                    last_seen=device["last_seen"],
                    total_cycles=device["total_cycles"],
                    last_health_score=device["last_health_score"],
                )
                for device in devices
            ]
        }


@router.put("/devices/{device_id}")
async def update_device(
        device_id: str,
        data: UpdateDeviceRequest,
        x_user_id: str = Header(...)
):
    parsed_device_id = parse_uuid_or_400(device_id, "device_id")
    user_id = parse_uuid_or_400(x_user_id, "X-User-Id")

    async with get_db_session() as session:
        try:
            result = await session.execute(
                select(Device).where(
                    Device.device_id == parsed_device_id,
                    Device.user_id == user_id,
                )
            )
            device = result.scalar_one_or_none()

            if device is None:
                raise HTTPException(status_code=403, detail="Device not found or access denied")

            device.device_name = data.device_name
            await session.commit()

            return {"status": "updated", "device_id": device_id, "device_name": data.device_name}
        except Exception:
            await session.rollback()
            raise


@router.delete("/devices/{device_id}")
async def delete_device(device_id: str, x_user_id: str = Header(...)):
    parsed_device_id = parse_uuid_or_400(device_id, "device_id")
    user_id = parse_uuid_or_400(x_user_id, "X-User-Id")

    async with get_db_session() as session:
        try:
            result = await session.execute(
                delete(Device)
                .where(
                    Device.device_id == parsed_device_id,
                    Device.user_id == user_id,
                )
                .returning(Device.device_id)
            )
            deleted_device_id = result.scalar_one_or_none()

            if deleted_device_id is None:
                raise HTTPException(status_code=403, detail="Device not found or access denied")

            await session.commit()

            return {"status": "deleted", "device_id": str(deleted_device_id)}
        except Exception:
            await session.rollback()
            raise
