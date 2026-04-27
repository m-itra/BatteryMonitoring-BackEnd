from datetime import datetime
from typing import Annotated, List, Optional

from pydantic import BaseModel, StringConstraints

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class DeviceInfo(BaseModel):
    device_id: str
    device_name: str
    created_at: datetime
    last_seen: datetime
    current_charge_percent: Optional[float] = None
    current_net_power_mw: Optional[int] = None
    current_soe_percent: Optional[float] = None
    current_soh_capacity_percent: Optional[float] = None
    current_soh_energy_percent: Optional[float] = None
    reference_capacity_mwh: Optional[int] = None
    reference_capacity_source: Optional[str] = None
    total_cycles: int
    has_active_session: bool


class ActiveSessionInfo(BaseModel):
    device_id: str
    started_at_client: datetime
    started_at_server: datetime
    last_client_time: datetime
    last_server_received_at: datetime
    start_charge_percent: float
    current_charge_percent: float
    discharged_energy_mwh: float
    duration_seconds: int
    pending_transition: str


class SessionInfo(BaseModel):
    session_id: str
    device_id: str
    boot_session_id: str
    started_at_client: datetime
    ended_at_client: datetime
    started_at_server: datetime
    ended_at_server: datetime
    start_charge_percent: float
    end_charge_percent: float
    discharge_delta_percent: float
    discharged_energy_mwh: float
    duration_seconds: int
    avg_load_mw: Optional[float] = None
    status: str
    equivalent_cycle_id: Optional[str] = None


class CycleInfo(BaseModel):
    cycle_id: str
    device_id: str
    started_at_client: datetime
    ended_at_client: datetime
    session_count: int
    total_discharge_percent: float
    total_energy_mwh: float
    total_duration_seconds: int
    avg_load_mw: Optional[float] = None
    reference_capacity_mwh_used: int
    full_charge_capacity_mwh_at_cycle_end: Optional[int] = None
    soh_capacity_percent: Optional[float] = None
    degradation_capacity_percent: Optional[float] = None
    soh_energy_percent: Optional[float] = None
    degradation_energy_percent: Optional[float] = None
    is_excluded: bool = False
    excluded_at: Optional[datetime] = None
    created_at: datetime


class CycleExclusionResponse(BaseModel):
    status: str
    message: str
    device_id: str
    cycle_id: str
    is_excluded: bool
    excluded_at: Optional[datetime] = None


class CycleDeletionResponse(BaseModel):
    status: str
    message: str
    device_id: str
    cycle_id: str
    deleted_sessions: int


class CapacityHistoryPoint(BaseModel):
    recorded_at: datetime
    full_charge_capacity_mwh: Optional[int] = None
    soh_capacity_percent: Optional[float] = None
    soh_energy_percent: Optional[float] = None
    degradation_capacity_percent: Optional[float] = None
    degradation_energy_percent: Optional[float] = None


class UpdateDeviceRequest(BaseModel):
    device_name: NonEmptyStr


class AnalyticsResponse(BaseModel):
    user: dict
    devices: List[DeviceInfo]
    recent_cycles: List[CycleInfo]
    total_cycles: int


class AdminBatteryStatsResponse(BaseModel):
    devices_count: int
    active_sessions_count: int
    completed_sessions_count: int
    interrupted_sessions_count: int
    equivalent_cycles_count: int
    excluded_cycles_count: int


class DeviceAnalyticsResponse(BaseModel):
    device: DeviceInfo
    active_session: Optional[ActiveSessionInfo] = None
    recent_sessions: List[SessionInfo]
    cycles: List[CycleInfo]
    capacity_history: List[CapacityHistoryPoint]
