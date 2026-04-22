from fastapi import APIRouter, Header, HTTPException, Query
from sqlalchemy import delete, select

from app.db.connection import get_db_session
from app.db.models import BatteryActiveSession, BatteryEquivalentCycle, BatterySession, Device
from app.db.query_helpers import (
    build_active_session_info,
    build_capacity_history_point,
    build_cycle_info,
    build_device_info,
    build_session_info,
    device_summary_statement,
    parse_uuid_or_400,
)
from app.models import DeviceAnalyticsResponse, UpdateDeviceRequest

router = APIRouter()


@router.get("/devices")
async def get_devices(x_user_id: str = Header(..., alias="X-User-Id")):
    user_id = parse_uuid_or_400(x_user_id, "X-User-Id")

    async with get_db_session() as session:
        result = await session.execute(device_summary_statement(user_id))
        devices = result.mappings().all()

        return {
            "devices": [build_device_info(device) for device in devices]
        }


@router.get("/devices/{device_id}", response_model=DeviceAnalyticsResponse)
async def get_device_analytics(
    device_id: str,
    x_user_id: str = Header(..., alias="X-User-Id"),
    session_limit: int = Query(default=50, ge=1, le=200),
    cycle_limit: int = Query(default=50, ge=1, le=200),
):
    parsed_device_id = parse_uuid_or_400(device_id, "device_id")
    user_id = parse_uuid_or_400(x_user_id, "X-User-Id")

    async with get_db_session() as session:
        device_result = await session.execute(device_summary_statement(user_id, parsed_device_id))
        device_row = device_result.mappings().one_or_none()

        if device_row is None:
            raise HTTPException(status_code=404, detail="Device not found")

        active_session_result = await session.execute(
            select(BatteryActiveSession).where(
                BatteryActiveSession.device_id == parsed_device_id,
                BatteryActiveSession.user_id == user_id,
            )
        )
        active_session = active_session_result.scalar_one_or_none()

        sessions_result = await session.execute(
            select(BatterySession)
            .where(
                BatterySession.device_id == parsed_device_id,
                BatterySession.user_id == user_id,
            )
            .order_by(BatterySession.ended_at_client.desc())
            .limit(session_limit)
        )
        sessions = sessions_result.scalars().all()

        cycles_result = await session.execute(
            select(BatteryEquivalentCycle)
            .where(
                BatteryEquivalentCycle.device_id == parsed_device_id,
                BatteryEquivalentCycle.user_id == user_id,
            )
            .order_by(BatteryEquivalentCycle.ended_at_client.desc())
            .limit(cycle_limit)
        )
        cycles = cycles_result.scalars().all()

        return DeviceAnalyticsResponse(
            device=build_device_info(device_row),
            active_session=build_active_session_info(active_session),
            recent_sessions=[build_session_info(battery_session) for battery_session in sessions],
            cycles=[build_cycle_info(cycle) for cycle in cycles],
            capacity_history=[build_capacity_history_point(cycle) for cycle in cycles],
        )


@router.put("/devices/{device_id}")
async def update_device(
    device_id: str,
    data: UpdateDeviceRequest,
    x_user_id: str = Header(..., alias="X-User-Id"),
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
                raise HTTPException(status_code=404, detail="Device not found")

            device.device_name = data.device_name
            await session.commit()

            return {"status": "updated", "device_id": device_id, "device_name": data.device_name}
        except HTTPException:
            await session.rollback()
            raise
        except Exception:
            await session.rollback()
            raise


@router.delete("/devices/{device_id}")
async def delete_device(device_id: str, x_user_id: str = Header(..., alias="X-User-Id")):
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
                raise HTTPException(status_code=404, detail="Device not found")

            await session.commit()

            return {"status": "deleted", "device_id": str(deleted_device_id)}
        except HTTPException:
            await session.rollback()
            raise
        except Exception:
            await session.rollback()
            raise
