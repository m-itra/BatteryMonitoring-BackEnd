from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Device


def parse_uuid(value: str) -> Optional[UUID]:
    try:
        return UUID(value)
    except (TypeError, ValueError):
        return None


async def create_device(session: AsyncSession, device_id: str, device_name: str, user_id: str):
    device = Device(
        device_id=UUID(device_id),
        user_id=UUID(user_id),
        device_name=device_name,
    )
    session.add(device)
    await session.flush()


async def get_device_by_id(session: AsyncSession, device_id: str):
    parsed_device_id = parse_uuid(device_id)
    if parsed_device_id is None:
        return None

    device = await session.get(Device, parsed_device_id)
    if device is None:
        return None

    return {
        "device_id": str(device.device_id),
        "user_id": str(device.user_id),
        "device_name": device.device_name,
    }
