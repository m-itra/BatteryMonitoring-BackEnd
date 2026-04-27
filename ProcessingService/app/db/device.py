from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Device
from app.models.battery import BatterySample


def parse_uuid(value: str) -> Optional[UUID]:
    try:
        return UUID(value)
    except (TypeError, ValueError):
        return None


async def create_device(
    session: AsyncSession,
    device_id: str,
    device_name: str,
    user_id: str,
    battery_id: Optional[str] = None,
    reference_capacity_mwh: Optional[int] = None,
) -> Device:
    device = Device(
        device_id=UUID(device_id),
        user_id=UUID(user_id),
        device_name=device_name,
        battery_id=battery_id,
        reference_capacity_mwh=reference_capacity_mwh,
        reference_capacity_source="user" if reference_capacity_mwh is not None else None,
    )
    session.add(device)
    await session.flush()
    return device


async def get_device_record_by_id(
    session: AsyncSession,
    device_id: str,
    *,
    for_update: bool = False,
) -> Optional[Device]:
    parsed_device_id = parse_uuid(device_id)
    if parsed_device_id is None:
        return None

    statement = select(Device).where(Device.device_id == parsed_device_id)
    if for_update:
        statement = statement.with_for_update()

    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def get_device_by_id(session: AsyncSession, device_id: str):
    device = await get_device_record_by_id(session, device_id)
    if device is None:
        return None

    return {
        "device_id": str(device.device_id),
        "user_id": str(device.user_id),
        "device_name": device.device_name,
    }


async def delete_devices_by_user_id(session: AsyncSession, user_id: str) -> int:
    parsed_user_id = parse_uuid(user_id)
    if parsed_user_id is None:
        return 0

    result = await session.execute(
        delete(Device)
        .where(Device.user_id == parsed_user_id)
        .returning(Device.device_id)
    )
    deleted_device_ids = result.scalars().all()
    await session.flush()
    return len(deleted_device_ids)


def _should_use_design_capacity(
    design_capacity_mwh: Optional[int],
    full_charge_capacity_mwh: Optional[int],
) -> bool:
    return (
        design_capacity_mwh is not None
        and full_charge_capacity_mwh is not None
        and design_capacity_mwh >= full_charge_capacity_mwh
    )


def update_device_reference_capacity(
    device: Device,
    *,
    requested_reference_capacity_mwh: Optional[int],
    design_capacity_mwh: Optional[int],
    full_charge_capacity_mwh: Optional[int],
) -> None:
    if requested_reference_capacity_mwh is not None:
        device.reference_capacity_mwh = requested_reference_capacity_mwh
        device.reference_capacity_source = "user"
        return

    if device.reference_capacity_source == "user" and device.reference_capacity_mwh is not None:
        return

    if _should_use_design_capacity(design_capacity_mwh, full_charge_capacity_mwh):
        device.reference_capacity_mwh = design_capacity_mwh
        device.reference_capacity_source = "design"


def update_device_snapshot(
    device: Device,
    *,
    sample: BatterySample,
    received_at: datetime,
    battery_id: Optional[str],
    requested_reference_capacity_mwh: Optional[int],
) -> None:
    if battery_id is not None:
        device.battery_id = battery_id

    device.last_seen = received_at
    device.last_client_time = sample.client_time
    device.last_boot_session_id = sample.boot_session_id
    device.last_sample_seq = sample.sample_seq
    device.last_ac_connected = sample.ac_connected
    device.last_is_charging = sample.is_charging
    device.last_charge_percent = sample.charge_percent
    device.last_full_charge_capacity_mwh = sample.full_charge_capacity_mwh
    device.last_remaining_capacity_mwh = sample.remaining_capacity_mwh
    device.last_net_power_mw = sample.net_power_mw

    update_device_reference_capacity(
        device,
        requested_reference_capacity_mwh=requested_reference_capacity_mwh,
        design_capacity_mwh=sample.design_capacity_mwh,
        full_charge_capacity_mwh=sample.full_charge_capacity_mwh,
    )
