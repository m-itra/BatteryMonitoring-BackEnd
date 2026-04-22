from typing import Any, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, case, func, select

from app.db.models import BatteryActiveSession, BatteryEquivalentCycle, BatterySession, Device
from app.models import (
    ActiveSessionInfo,
    CapacityHistoryPoint,
    CycleInfo,
    DeviceInfo,
    SessionInfo,
)


def parse_uuid_or_400(value: str, field_name: str) -> UUID:
    try:
        return UUID(value)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}")


def _round(value: Optional[float], digits: int = 4) -> Optional[float]:
    if value is None:
        return None
    return round(value, digits)


def device_summary_statement(user_id: UUID, device_id: Optional[UUID] = None):
    total_cycles = (
        select(func.count(BatteryEquivalentCycle.cycle_id))
        .where(BatteryEquivalentCycle.device_id == Device.device_id)
        .correlate(Device)
        .scalar_subquery()
    )

    last_soh_energy = (
        select(BatteryEquivalentCycle.soh_energy_percent)
        .where(BatteryEquivalentCycle.device_id == Device.device_id)
        .order_by(BatteryEquivalentCycle.ended_at_client.desc())
        .limit(1)
        .correlate(Device)
        .scalar_subquery()
    )

    has_active_session = (
        select(BatteryActiveSession.device_id)
        .where(BatteryActiveSession.device_id == Device.device_id)
        .correlate(Device)
        .exists()
    )

    current_soe_percent = case(
        (
            and_(
                Device.last_remaining_capacity_mwh.is_not(None),
                Device.last_full_charge_capacity_mwh.is_not(None),
                Device.last_full_charge_capacity_mwh > 0,
            ),
            (Device.last_remaining_capacity_mwh * 100.0) / Device.last_full_charge_capacity_mwh,
        ),
        else_=None,
    )

    current_soh_capacity_percent = case(
        (
            and_(
                Device.reference_capacity_mwh.is_not(None),
                Device.reference_capacity_mwh > 0,
                Device.last_full_charge_capacity_mwh.is_not(None),
            ),
            (Device.last_full_charge_capacity_mwh * 100.0) / Device.reference_capacity_mwh,
        ),
        else_=None,
    )

    statement = (
        select(
            Device.device_id,
            Device.device_name,
            Device.created_at,
            Device.last_seen,
            Device.last_charge_percent,
            Device.last_net_power_mw,
            Device.reference_capacity_mwh,
            Device.reference_capacity_source,
            total_cycles.label("total_cycles"),
            last_soh_energy.label("current_soh_energy_percent"),
            has_active_session.label("has_active_session"),
            current_soe_percent.label("current_soe_percent"),
            current_soh_capacity_percent.label("current_soh_capacity_percent"),
        )
        .where(Device.user_id == user_id)
        .order_by(Device.last_seen.desc())
    )

    if device_id is not None:
        statement = statement.where(Device.device_id == device_id)

    return statement


def build_device_info(device_row: Any) -> DeviceInfo:
    return DeviceInfo(
        device_id=str(device_row["device_id"]),
        device_name=device_row["device_name"],
        created_at=device_row["created_at"],
        last_seen=device_row["last_seen"],
        current_charge_percent=_round(device_row["last_charge_percent"], 2),
        current_net_power_mw=device_row["last_net_power_mw"],
        current_soe_percent=_round(device_row["current_soe_percent"], 4),
        current_soh_capacity_percent=_round(device_row["current_soh_capacity_percent"], 4),
        current_soh_energy_percent=_round(device_row["current_soh_energy_percent"], 4),
        reference_capacity_mwh=device_row["reference_capacity_mwh"],
        reference_capacity_source=device_row["reference_capacity_source"],
        total_cycles=device_row["total_cycles"] or 0,
        has_active_session=bool(device_row["has_active_session"]),
    )


def build_active_session_info(active_session: Optional[BatteryActiveSession]) -> Optional[ActiveSessionInfo]:
    if active_session is None:
        return None

    return ActiveSessionInfo(
        device_id=str(active_session.device_id),
        started_at_client=active_session.started_at_client,
        started_at_server=active_session.started_at_server,
        last_client_time=active_session.last_client_time,
        last_server_received_at=active_session.last_server_received_at,
        start_charge_percent=_round(active_session.start_charge_percent, 4) or 0.0,
        current_charge_percent=_round(active_session.current_charge_percent, 4) or 0.0,
        discharged_energy_mwh=_round(active_session.discharged_energy_mwh, 4) or 0.0,
        duration_seconds=active_session.duration_seconds,
        pending_transition=active_session.pending_transition,
    )


def build_session_info(battery_session: BatterySession) -> SessionInfo:
    return SessionInfo(
        session_id=str(battery_session.session_id),
        device_id=str(battery_session.device_id),
        boot_session_id=str(battery_session.boot_session_id),
        started_at_client=battery_session.started_at_client,
        ended_at_client=battery_session.ended_at_client,
        started_at_server=battery_session.started_at_server,
        ended_at_server=battery_session.ended_at_server,
        start_charge_percent=_round(battery_session.start_charge_percent, 4) or 0.0,
        end_charge_percent=_round(battery_session.end_charge_percent, 4) or 0.0,
        discharge_delta_percent=_round(battery_session.discharge_delta_percent, 4) or 0.0,
        discharged_energy_mwh=_round(battery_session.discharged_energy_mwh, 4) or 0.0,
        duration_seconds=battery_session.duration_seconds,
        avg_load_mw=_round(battery_session.avg_load_mw, 4),
        status=battery_session.status,
        equivalent_cycle_id=(
            str(battery_session.equivalent_cycle_id)
            if battery_session.equivalent_cycle_id is not None
            else None
        ),
    )


def build_cycle_info(cycle: BatteryEquivalentCycle) -> CycleInfo:
    return CycleInfo(
        cycle_id=str(cycle.cycle_id),
        device_id=str(cycle.device_id),
        started_at_client=cycle.started_at_client,
        ended_at_client=cycle.ended_at_client,
        session_count=cycle.session_count,
        total_discharge_percent=_round(cycle.total_discharge_percent, 4) or 0.0,
        total_energy_mwh=_round(cycle.total_energy_mwh, 4) or 0.0,
        total_duration_seconds=cycle.total_duration_seconds,
        avg_load_mw=_round(cycle.avg_load_mw, 4),
        reference_capacity_mwh_used=cycle.reference_capacity_mwh_used,
        full_charge_capacity_mwh_at_cycle_end=cycle.full_charge_capacity_mwh_at_cycle_end,
        soh_capacity_percent=_round(cycle.soh_capacity_percent, 4),
        degradation_capacity_percent=_round(cycle.degradation_capacity_percent, 4),
        soh_energy_percent=_round(cycle.soh_energy_percent, 4),
        degradation_energy_percent=_round(cycle.degradation_energy_percent, 4),
        created_at=cycle.created_at,
    )


def build_capacity_history_point(cycle: BatteryEquivalentCycle) -> CapacityHistoryPoint:
    return CapacityHistoryPoint(
        recorded_at=cycle.ended_at_client,
        full_charge_capacity_mwh=cycle.full_charge_capacity_mwh_at_cycle_end,
        soh_capacity_percent=_round(cycle.soh_capacity_percent, 4),
        soh_energy_percent=_round(cycle.soh_energy_percent, 4),
        degradation_capacity_percent=_round(cycle.degradation_capacity_percent, 4),
        degradation_energy_percent=_round(cycle.degradation_energy_percent, 4),
    )
