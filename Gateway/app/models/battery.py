from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class BatterySample(BaseModel):
    boot_session_id: UUID
    sample_seq: int = Field(ge=1)
    client_time: datetime
    ac_connected: bool
    is_charging: bool
    charge_percent: float = Field(ge=0, le=100)
    remaining_capacity_mwh: Optional[int] = Field(default=None, ge=0)
    full_charge_capacity_mwh: Optional[int] = Field(default=None, ge=0)
    design_capacity_mwh: Optional[int] = Field(default=None, ge=0)
    voltage_mv: Optional[int] = None
    net_power_mw: int
    temperature_c: Optional[float] = None
    status: Optional[str] = None

    @field_validator("status", mode="before")
    @classmethod
    def optional_status_must_not_be_blank(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value

        stripped = value.strip()
        return stripped or None


class BatteryLogBatchRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "device_id": "74fd26ad-5f67-489c-a17b-7f8eef3d9612",
                "device_name": "Office Laptop",
                "battery_id": r"\\?\acpi#pnp0c0a#battery",
                "reference_capacity_mwh": 40000,
                "samples": [
                    {
                        "boot_session_id": "3a0481a3-ab9b-4a9d-8d82-0f85cf822dbc",
                        "sample_seq": 1,
                        "client_time": "2026-04-21T13:40:17.967102",
                        "ac_connected": True,
                        "is_charging": True,
                        "charge_percent": 94.7,
                        "remaining_capacity_mwh": 37648,
                        "full_charge_capacity_mwh": 39735,
                        "design_capacity_mwh": 39735,
                        "voltage_mv": 12940,
                        "net_power_mw": -11793,
                        "temperature_c": None,
                        "status": "charging,ac_online",
                    }
                ],
            }
        }
    )

    device_id: Optional[str] = None
    device_name: Optional[str] = None
    battery_id: Optional[str] = None
    reference_capacity_mwh: Optional[int] = Field(default=None, ge=1)
    samples: list[BatterySample] = Field(min_length=1)

    @field_validator("device_id", "device_name", "battery_id")
    @classmethod
    def optional_text_must_not_be_blank(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value

        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def check_device_info(self):
        if not self.device_id and not self.device_name:
            raise ValueError("device_name is required when device_id is not provided")
        return self


class BatteryLogBatchResponse(BaseModel):
    status: str
    message: str
    device_id: str
    processed_samples: int
    duplicate_samples: int
    completed_sessions: int
    completed_cycles: int
