from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.device import update_device_snapshot
from app.db.models import BatteryActiveSession, BatteryEquivalentCycle, BatterySession, Device
from app.models.battery import BatteryLogBatchRequest, BatterySample

INTERRUPTED_TIMEOUT_SECONDS = 120


@dataclass
class BatchIngestResult:
    device_id: str
    processed_samples: int = 0
    duplicate_samples: int = 0
    completed_sessions: int = 0
    completed_cycles: int = 0


def _ordered_samples(samples: list[BatterySample]) -> list[BatterySample]:
    return sorted(samples, key=lambda sample: (sample.client_time, sample.sample_seq))


def _is_duplicate(device: Device, sample: BatterySample) -> bool:
    return (
        device.last_boot_session_id == sample.boot_session_id
        and device.last_sample_seq is not None
        and sample.sample_seq <= device.last_sample_seq
    )


def _integrate_discharge(
    previous_client_time: Optional[datetime],
    previous_net_power_mw: Optional[int],
    current_client_time: datetime,
) -> tuple[float, int]:
    if previous_client_time is None or previous_net_power_mw is None:
        return 0.0, 0

    dt_seconds = max(int((current_client_time - previous_client_time).total_seconds()), 0)
    if dt_seconds == 0:
        return 0.0, 0

    energy_step_mwh = max(previous_net_power_mw, 0) * (dt_seconds / 3600)
    return energy_step_mwh, dt_seconds


async def _get_active_session(
    session: AsyncSession,
    device_id: UUID,
) -> Optional[BatteryActiveSession]:
    result = await session.execute(
        select(BatteryActiveSession)
        .where(BatteryActiveSession.device_id == device_id)
        .with_for_update()
    )
    return result.scalar_one_or_none()


def _avg_load_mw(energy_mwh: float, duration_seconds: int) -> Optional[float]:
    if duration_seconds <= 0:
        return None

    return energy_mwh / (duration_seconds / 3600)


async def _delete_active_session(
    session: AsyncSession,
    active_session: BatteryActiveSession,
) -> None:
    await session.delete(active_session)
    await session.flush()


async def _close_active_session(
    session: AsyncSession,
    device: Device,
    active_session: BatteryActiveSession,
    *,
    status: str,
    ended_at_client: datetime,
    ended_at_server: datetime,
    end_charge_percent: float,
) -> BatterySession:
    discharge_delta_percent = max(active_session.start_charge_percent - end_charge_percent, 0.0)
    avg_load_mw = _avg_load_mw(active_session.discharged_energy_mwh, active_session.duration_seconds)

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
        avg_load_mw=round(avg_load_mw, 4) if avg_load_mw is not None else None,
        status=status,
    )
    session.add(battery_session)
    await session.flush()
    await _delete_active_session(session, active_session)

    if status == "completed":
        return battery_session

    return battery_session


def _ensure_reference_capacity(device: Device, fallback_energy_mwh: float) -> int:
    if device.reference_capacity_mwh is not None and device.reference_capacity_mwh > 0:
        return device.reference_capacity_mwh

    baseline_capacity_mwh = max(int(round(fallback_energy_mwh)), 1)
    if device.baseline_capacity_mwh is None:
        device.baseline_capacity_mwh = baseline_capacity_mwh

    device.reference_capacity_mwh = device.baseline_capacity_mwh
    device.reference_capacity_source = "baseline"
    return device.reference_capacity_mwh


async def _create_equivalent_cycles(
    session: AsyncSession,
    device: Device,
) -> int:
    created_cycles = 0

    while True:
        result = await session.execute(
            select(BatterySession)
            .where(
                BatterySession.device_id == device.device_id,
                BatterySession.status == "completed",
                BatterySession.equivalent_cycle_id.is_(None),
                BatterySession.discharge_delta_percent > 0,
            )
            .order_by(BatterySession.ended_at_client.asc(), BatterySession.session_id.asc())
            .with_for_update()
        )
        pending_sessions = result.scalars().all()

        if not pending_sessions:
            break

        accumulated_percent = 0.0
        total_energy_mwh = 0.0
        total_duration_seconds = 0
        selected_sessions: list[BatterySession] = []
        cycle_started_at: Optional[datetime] = None
        cycle_ended_at: Optional[datetime] = None

        for pending_session in pending_sessions:
            remaining_percent = 100.0 - accumulated_percent
            session_percent = pending_session.discharge_delta_percent

            if cycle_started_at is None:
                cycle_started_at = pending_session.started_at_client

            selected_sessions.append(pending_session)
            cycle_ended_at = pending_session.ended_at_client

            if session_percent < remaining_percent:
                accumulated_percent += session_percent
                total_energy_mwh += pending_session.discharged_energy_mwh
                total_duration_seconds += pending_session.duration_seconds
                continue

            usage_ratio = remaining_percent / session_percent if session_percent > 0 else 0.0
            total_energy_mwh += pending_session.discharged_energy_mwh * usage_ratio
            total_duration_seconds += int(round(pending_session.duration_seconds * usage_ratio))
            accumulated_percent = 100.0
            break

        if accumulated_percent < 100.0 or cycle_started_at is None or cycle_ended_at is None:
            break

        reference_capacity_mwh = _ensure_reference_capacity(device, total_energy_mwh)
        full_charge_capacity_mwh = device.last_full_charge_capacity_mwh

        soh_capacity_percent = None
        degradation_capacity_percent = None
        if full_charge_capacity_mwh is not None and reference_capacity_mwh > 0:
            soh_capacity_percent = (full_charge_capacity_mwh / reference_capacity_mwh) * 100
            degradation_capacity_percent = max(0.0, 100.0 - soh_capacity_percent)

        soh_energy_percent = None
        degradation_energy_percent = None
        if reference_capacity_mwh > 0:
            soh_energy_percent = (total_energy_mwh / reference_capacity_mwh) * 100
            degradation_energy_percent = max(0.0, 100.0 - soh_energy_percent)

        avg_load_mw = _avg_load_mw(total_energy_mwh, total_duration_seconds)
        cycle = BatteryEquivalentCycle(
            device_id=device.device_id,
            user_id=device.user_id,
            started_at_client=cycle_started_at,
            ended_at_client=cycle_ended_at,
            session_count=len(selected_sessions),
            total_discharge_percent=100.0,
            total_energy_mwh=round(total_energy_mwh, 4),
            total_duration_seconds=total_duration_seconds,
            avg_load_mw=round(avg_load_mw, 4) if avg_load_mw is not None else None,
            reference_capacity_mwh_used=reference_capacity_mwh,
            full_charge_capacity_mwh_at_cycle_end=full_charge_capacity_mwh,
            soh_capacity_percent=round(soh_capacity_percent, 4) if soh_capacity_percent is not None else None,
            degradation_capacity_percent=(
                round(degradation_capacity_percent, 4)
                if degradation_capacity_percent is not None
                else None
            ),
            soh_energy_percent=round(soh_energy_percent, 4) if soh_energy_percent is not None else None,
            degradation_energy_percent=(
                round(degradation_energy_percent, 4)
                if degradation_energy_percent is not None
                else None
            ),
        )
        session.add(cycle)
        await session.flush()

        for selected_session in selected_sessions:
            selected_session.equivalent_cycle_id = cycle.cycle_id

        created_cycles += 1

    return created_cycles


async def _interrupt_stale_session_if_needed(
    session: AsyncSession,
    device: Device,
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
        await _delete_active_session(session, active_session)
        return None

    await _close_active_session(
        session,
        device,
        active_session,
        status="interrupted",
        ended_at_client=active_session.last_client_time,
        ended_at_server=active_session.last_server_received_at,
        end_charge_percent=active_session.current_charge_percent,
    )
    return None


async def _handle_start_candidate(
    session: AsyncSession,
    active_session: BatteryActiveSession,
    *,
    device: Device,
    sample: BatterySample,
    received_at: datetime,
) -> Optional[BatteryActiveSession]:
    if sample.boot_session_id != active_session.boot_session_id or sample.ac_connected:
        await _delete_active_session(session, active_session)
        return None

    energy_step_mwh, duration_step_seconds = _integrate_discharge(
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


async def _handle_active_session(
    active_session: BatteryActiveSession,
    *,
    device: Device,
    sample: BatterySample,
    received_at: datetime,
) -> BatteryActiveSession:
    energy_step_mwh, duration_step_seconds = _integrate_discharge(
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


async def _handle_finish_candidate(
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

    await _close_active_session(
        session,
        device,
        active_session,
        status="completed",
        ended_at_client=ended_at_client,
        ended_at_server=ended_at_server,
        end_charge_percent=end_charge_percent,
    )
    completed_cycles = await _create_equivalent_cycles(session, device)
    return None, 1, completed_cycles


async def process_battery_batch(
    session: AsyncSession,
    *,
    device: Device,
    request_data: BatteryLogBatchRequest,
) -> BatchIngestResult:
    result = BatchIngestResult(device_id=str(device.device_id))
    active_session = await _get_active_session(session, device.device_id)

    for sample in _ordered_samples(request_data.samples):
        received_at = datetime.now()

        if _is_duplicate(device, sample):
            result.duplicate_samples += 1
            continue

        active_session = await _interrupt_stale_session_if_needed(
            session,
            device,
            active_session,
            received_at=received_at,
            sample=sample,
        )

        if active_session is None:
            if not sample.ac_connected:
                active_session = BatteryActiveSession(
                    device_id=device.device_id,
                    user_id=device.user_id,
                    boot_session_id=sample.boot_session_id,
                    started_at_client=sample.client_time,
                    started_at_server=received_at,
                    last_client_time=sample.client_time,
                    last_server_received_at=received_at,
                    last_sample_seq=sample.sample_seq,
                    start_charge_percent=sample.charge_percent,
                    current_charge_percent=sample.charge_percent,
                    discharged_energy_mwh=0.0,
                    duration_seconds=0,
                    pending_transition="start_candidate",
                )
                session.add(active_session)
                await session.flush()
        elif active_session.pending_transition == "start_candidate":
            active_session = await _handle_start_candidate(
                session,
                active_session,
                device=device,
                sample=sample,
                received_at=received_at,
            )
        elif active_session.pending_transition == "finish_candidate":
            active_session, completed_sessions, completed_cycles = await _handle_finish_candidate(
                session,
                device,
                active_session,
                sample=sample,
                received_at=received_at,
            )
            result.completed_sessions += completed_sessions
            result.completed_cycles += completed_cycles
        else:
            active_session = await _handle_active_session(
                active_session,
                device=device,
                sample=sample,
                received_at=received_at,
            )

        update_device_snapshot(
            device,
            sample=sample,
            received_at=received_at,
            battery_id=request_data.battery_id,
            requested_reference_capacity_mwh=request_data.reference_capacity_mwh,
        )
        result.processed_samples += 1

    await session.flush()
    return result
