from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Device(Base):
    __tablename__ = "devices"

    device_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    device_name: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text("NOW()"))
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text("NOW()"))


class BatteryCycle(Base):
    __tablename__ = "battery_cycles"

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
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    health_score: Mapped[Optional[float]] = mapped_column(Float)
    capacity_degradation: Mapped[Optional[float]] = mapped_column(Float)
    cycle_count: Mapped[int] = mapped_column(Integer, nullable=False)
    charge_cycles_equivalent: Mapped[Optional[float]] = mapped_column(Float)
    min_level: Mapped[Optional[int]] = mapped_column(Integer)
    max_level: Mapped[Optional[int]] = mapped_column(Integer)
    avg_discharge_rate: Mapped[Optional[float]] = mapped_column(Float)
    avg_charge_rate: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text("NOW()"))
