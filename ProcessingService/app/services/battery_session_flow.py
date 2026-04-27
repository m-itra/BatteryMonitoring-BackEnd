from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import MIN_SESSION_DISCHARGE_PERCENT
from app.db.models import BatteryActiveSession, BatterySession, Device
from app.models.battery import BatterySample

from app.services.battery_cycle_builder import create_equivalent_cycles
from app.services.battery_math import avg_load_mw, integrate_discharge

INTERRUPTED_TIMEOUT_SECONDS = 120


def should_persist_session(discharge_delta_percent: float) -> bool:
    return discharge_delta_percent >= MIN_SESSION_DISCHARGE_PERCENT


async def get_active_session(
    session: AsyncSession,
    device_id: UUID,
) -> Optional[BatteryActiveSession]:
    result = await session.execute(
        select(BatteryActiveSession)
        .where(BatteryActiveSession.device_id == device_id)
        .with_for_update()
    )
    return result.scalar_one_or_none()


async def delete_active_session(
    session: AsyncSession,
    active_session: BatteryActiveSession,
) -> None:
    await session.delete(active_session)
    await session.flush()


async def close_active_session(
    session: AsyncSession,
    active_session: BatteryActiveSession,
    *,
    status: str,
    ended_at_client: datetime,
    ended_at_server: datetime,
    end_charge_percent: float,
) -> Optional[BatterySession]:
    discharge_delta_percent = max(active_session.start_charge_percent - end_charge_percent, 0.0)

    if not should_persist_session(discharge_delta_percent):
        await delete_active_session(session, active_session)
        return None

    average_load_mw = avg_load_mw(active_session.discharged_energy_mwh, active_session.duration_seconds)

    battery_session = BatterySession(
        device_id=active_session.device_id,
        user_id=active_session.user_id,
        boot_session_id=active_session.boot_session_id,
        started_at_client=active_session.started_at_client,
        ended_at_client=ended_at_client,
        started_at_server=active_session.started_at_server,
        ended_at_server=ended_at_server,
        start_charge_percent=active_session.start_charge_percent,
        end_charge_percent=end_charge_percent,
        discharge_delta_percent=round(discharge_delta_percent, 4),
        discharged_energy_mwh=round(active_session.discharged_energy_mwh, 4),
        duration_seconds=active_session.duration_seconds,
        avg_load_mw=round(average_load_mw, 4) if average_load_mw is not None else None,
        status=status,
    )
    session.add(battery_session)
    await session.flush()
    await delete_active_session(session, active_session)
    return battery_session


async def interrupt_stale_session_if_needed(
    session: AsyncSession,
    active_session: Optional[BatteryActiveSession],
    *,
    received_at: datetime,
    sample: BatterySample,
) -> Optional[BatteryActiveSession]:
    if active_session is None:
        return None

    session_is_stale = (
        received_at - active_session.last_server_received_at
    ).total_seconds() > INTERRUPTED_TIMEOUT_SECONDS
    boot_changed = sample.boot_session_id != active_session.boot_session_id

    if not session_is_stale and not boot_changed:
        return active_session

    if active_session.pending_transition == "start_candidate":
        await delete_active_session(session, active_session)
        return None

    await close_active_session(
        session,
        active_session,
        status="interrupted",
        ended_at_client=active_session.last_client_time,
        ended_at_server=active_session.last_server_received_at,
        end_charge_percent=active_session.current_charge_percent,
    )
    return None


async def handle_start_candidate(
    session: AsyncSession,
    active_session: BatteryActiveSession,
    *,
    device: Device,
    sample: BatterySample,
    received_at: datetime,
) -> Optional[BatteryActiveSession]:
    if sample.boot_session_id != active_session.boot_session_id or sample.ac_connected:
        await delete_active_session(session, active_session)
        return None

    energy_step_mwh, duration_step_seconds = integrate_discharge(
        device.last_client_time,
        device.last_net_power_mw,
        sample.client_time,
    )
    active_session.discharged_energy_mwh += energy_step_mwh
    active_session.duration_seconds += duration_step_seconds
    active_session.pending_transition = "none"
    active_session.last_client_time = sample.client_time
    active_session.last_server_received_at = received_at
    active_session.last_sample_seq = sample.sample_seq
    active_session.current_charge_percent = sample.charge_percent
    active_session.pending_transition_at_client = None
    active_session.pending_transition_at_server = None
    active_session.pending_transition_charge_percent = None
    return active_session


async def handle_active_session(
    active_session: BatteryActiveSession,
    *,
    device: Device,
    sample: BatterySample,
    received_at: datetime,
) -> BatteryActiveSession:
    energy_step_mwh, duration_step_seconds = integrate_discharge(
        device.last_client_time,
        device.last_net_power_mw,
        sample.client_time,
    )
    active_session.discharged_energy_mwh += energy_step_mwh
    active_session.duration_seconds += duration_step_seconds
    active_session.last_client_time = sample.client_time
    active_session.last_server_received_at = received_at
    active_session.last_sample_seq = sample.sample_seq
    active_session.current_charge_percent = sample.charge_percent

    if sample.ac_connected:
        active_session.pending_transition = "finish_candidate"
        active_session.pending_transition_at_client = sample.client_time
        active_session.pending_transition_at_server = received_at
        active_session.pending_transition_charge_percent = sample.charge_percent

    return active_session


async def handle_finish_candidate(
    session: AsyncSession,
    device: Device,
    active_session: BatteryActiveSession,
    *,
    sample: BatterySample,
    received_at: datetime,
) -> tuple[Optional[BatteryActiveSession], int, int]:
    if not sample.ac_connected:
        active_session.pending_transition = "none"
        active_session.pending_transition_at_client = None
        active_session.pending_transition_at_server = None
        active_session.pending_transition_charge_percent = None
        active_session.last_client_time = sample.client_time
        active_session.last_server_received_at = received_at
        active_session.last_sample_seq = sample.sample_seq
        active_session.current_charge_percent = sample.charge_percent
        return active_session, 0, 0

    ended_at_client = active_session.pending_transition_at_client or active_session.last_client_time
    ended_at_server = active_session.pending_transition_at_server or active_session.last_server_received_at
    end_charge_percent = (
        active_session.pending_transition_charge_percent
        if active_session.pending_transition_charge_percent is not None
        else active_session.current_charge_percent
    )

    saved_session = await close_active_session(
        session,
        active_session,
        status="completed",
        ended_at_client=ended_at_client,
        ended_at_server=ended_at_server,
        end_charge_percent=end_charge_percent,
    )
    if saved_session is None:
        return None, 0, 0

    completed_cycles = await create_equivalent_cycles(session, device)
    return None, 1, completed_cycles
