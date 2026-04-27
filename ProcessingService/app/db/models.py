from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Device(Base):
    __tablename__ = "devices"
    __table_args__ = (
        Index("idx_devices_user_id", "user_id"),
    )

    device_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    device_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        server_default=text("'New device'"),
    )
    battery_id: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text("NOW()"))
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text("NOW()"))
    last_client_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_boot_session_id: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True))
    last_sample_seq: Mapped[Optional[int]] = mapped_column(Integer)
    last_ac_connected: Mapped[Optional[bool]] = mapped_column(Boolean)
    last_is_charging: Mapped[Optional[bool]] = mapped_column(Boolean)
    last_charge_percent: Mapped[Optional[float]] = mapped_column(Float)
    last_full_charge_capacity_mwh: Mapped[Optional[int]] = mapped_column(Integer)
    last_remaining_capacity_mwh: Mapped[Optional[int]] = mapped_column(Integer)
    last_net_power_mw: Mapped[Optional[int]] = mapped_column(Integer)
    reference_capacity_mwh: Mapped[Optional[int]] = mapped_column(Integer)
    reference_capacity_source: Mapped[Optional[str]] = mapped_column(String(20))
    baseline_capacity_mwh: Mapped[Optional[int]] = mapped_column(Integer)

class BatteryActiveSession(Base):
    __tablename__ = "battery_active_sessions"
    __table_args__ = (
        Index("idx_active_sessions_user_id", "user_id"),
    )

    device_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("devices.device_id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    boot_session_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    started_at_client: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    started_at_server: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_client_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_server_received_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_sample_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    start_charge_percent: Mapped[float] = mapped_column(Float, nullable=False)
    current_charge_percent: Mapped[float] = mapped_column(Float, nullable=False)
    discharged_energy_mwh: Mapped[float] = mapped_column(Float, nullable=False, server_default=text("0"))
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    pending_transition: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'none'"),
    )
    pending_transition_at_client: Mapped[Optional[datetime]] = mapped_column(DateTime)
    pending_transition_at_server: Mapped[Optional[datetime]] = mapped_column(DateTime)
    pending_transition_charge_percent: Mapped[Optional[float]] = mapped_column(Float)


class BatteryEquivalentCycle(Base):
    __tablename__ = "battery_equivalent_cycles"
    __table_args__ = (
        Index("idx_equivalent_cycles_user_id", "user_id"),
        Index("idx_equivalent_cycles_device_id", "device_id"),
        Index("idx_equivalent_cycles_ended_at", "ended_at_client"),
    )

    cycle_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    device_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("devices.device_id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    started_at_client: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ended_at_client: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    session_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_discharge_percent: Mapped[float] = mapped_column(Float, nullable=False)
    total_energy_mwh: Mapped[float] = mapped_column(Float, nullable=False)
    total_duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_load_mw: Mapped[Optional[float]] = mapped_column(Float)
    reference_capacity_mwh_used: Mapped[int] = mapped_column(Integer, nullable=False)
    full_charge_capacity_mwh_at_cycle_end: Mapped[Optional[int]] = mapped_column(Integer)
    soh_capacity_percent: Mapped[Optional[float]] = mapped_column(Float)
    degradation_capacity_percent: Mapped[Optional[float]] = mapped_column(Float)
    soh_energy_percent: Mapped[Optional[float]] = mapped_column(Float)
    degradation_energy_percent: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text("NOW()"))


class BatterySession(Base):
    __tablename__ = "battery_sessions"
    __table_args__ = (
        Index("idx_sessions_user_id", "user_id"),
        Index("idx_sessions_device_id", "device_id"),
        Index("idx_sessions_status", "status"),
        Index("idx_sessions_ended_at", "ended_at_client"),
        Index("idx_sessions_equivalent_cycle_id", "equivalent_cycle_id"),
    )

    session_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    device_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("devices.device_id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    boot_session_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    started_at_client: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ended_at_client: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    started_at_server: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ended_at_server: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    start_charge_percent: Mapped[float] = mapped_column(Float, nullable=False)
    end_charge_percent: Mapped[float] = mapped_column(Float, nullable=False)
    discharge_delta_percent: Mapped[float] = mapped_column(Float, nullable=False)
    discharged_energy_mwh: Mapped[float] = mapped_column(Float, nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_load_mw: Mapped[Optional[float]] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    equivalent_cycle_id: Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("battery_equivalent_cycles.cycle_id", ondelete="CASCADE"),
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text("NOW()"))
