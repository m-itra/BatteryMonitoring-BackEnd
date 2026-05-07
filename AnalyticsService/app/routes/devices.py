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


def _should_use_design_capacity(
    design_capacity_mwh: int | None,
    full_charge_capacity_mwh: int | None,
) -> bool:
    return (
        design_capacity_mwh is not None
        and full_charge_capacity_mwh is not None
        and design_capacity_mwh >= full_charge_capacity_mwh
    )


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
        active_cycles = [cycle for cycle in cycles if not cycle.is_excluded]

        return DeviceAnalyticsResponse(
            device=build_device_info(device_row),
            active_session=build_active_session_info(active_session),
            recent_sessions=[build_session_info(battery_session) for battery_session in sessions],
            cycles=[
                build_cycle_info(cycle, device_row["reference_capacity_mwh"])
                for cycle in cycles
            ],
            capacity_history=[
                build_capacity_history_point(cycle, device_row["reference_capacity_mwh"])
                for cycle in active_cycles
            ],
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

            if data.device_name is not None:
                device.device_name = data.device_name

            if data.reference_capacity_mwh is not None:
                if data.reference_capacity_mwh > 0:
                    device.reference_capacity_mwh = data.reference_capacity_mwh
                    device.reference_capacity_source = "user"
                else:
                    device.reference_capacity_mwh = None
                    device.reference_capacity_source = None
                    if _should_use_design_capacity(
                        device.last_design_capacity_mwh,
                        device.last_full_charge_capacity_mwh,
                    ):
                        device.reference_capacity_mwh = device.last_design_capacity_mwh
                        device.reference_capacity_source = "design"
            await session.commit()

            return {
                "status": "updated",
                "device_id": device_id,
                "device_name": device.device_name,
                "reference_capacity_mwh": device.reference_capacity_mwh,
                "reference_capacity_source": device.reference_capacity_source,
            }
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
