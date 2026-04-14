from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
REPOSITORY_DIR = PROJECT_DIR.parent
ENV_PATH = REPOSITORY_DIR / "Infrastructure" / ".env"
DEV_BATTERY_DATABASE_URL = "postgresql://admin:password@localhost:5433/batterydb"
DEV_ENVIRONMENTS = {"development", "dev", "local", "test"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = Field(default="development", validation_alias=AliasChoices("ENVIRONMENT", "APP_ENV"))
    battery_database_url: str = Field(
        default=DEV_BATTERY_DATABASE_URL,
        validation_alias=AliasChoices("BATTERY_DATABASE_URL", "DATABASE_URL"),
    )
    user_service_grpc_url: str = Field(default="localhost:50051", validation_alias="USER_SERVICE_GRPC_URL")

    @model_validator(mode="after")
    def validate_non_dev_settings(self):
        if self.environment.lower() in DEV_ENVIRONMENTS:
            return self

        if self.battery_database_url == DEV_BATTERY_DATABASE_URL:
            raise ValueError("BATTERY_DATABASE_URL must be set outside development")
        if self.user_service_grpc_url.startswith("localhost"):
            raise ValueError("USER_SERVICE_GRPC_URL must not point to localhost outside development")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

BATTERY_DATABASE_URL = settings.battery_database_url
USER_SERVICE_GRPC_URL = settings.user_service_grpc_url
