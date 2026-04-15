from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class BatteryLogRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "device_id": "my-laptop",
                "device_name": "MacBook Pro 2023",
                "battery_level": 85,
                "is_charging": False
            }
        }
    )

    device_id: Optional[str] = None
    device_name: Optional[str] = None
    battery_level: int = Field(ge=0, le=100)
    is_charging: bool
    timestamp: Optional[datetime] = None

    @field_validator("device_id", "device_name")
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


class SubmitResponse(BaseModel):
    status: str
    message: str
    device_id: str
    cycle_created: bool = False
