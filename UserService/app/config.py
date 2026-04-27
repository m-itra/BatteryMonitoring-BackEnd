from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
REPOSITORY_DIR = PROJECT_DIR.parent
ENV_PATH = REPOSITORY_DIR / "Infrastructure" / ".env"
DEV_JWT_SECRET = "dev-secret-change-me"
DEV_USER_DATABASE_URL = "postgresql://admin:password@localhost:5432/userdb"
DEV_ENVIRONMENTS = {"development", "dev", "local", "test"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = Field(default="development", validation_alias=AliasChoices("ENVIRONMENT", "APP_ENV"))
    user_database_url: str = Field(
        default=DEV_USER_DATABASE_URL,
        validation_alias=AliasChoices("USER_DATABASE_URL", "DATABASE_URL"),
    )
    jwt_secret: str = Field(
        default=DEV_JWT_SECRET,
        validation_alias=AliasChoices("JWT_SECRET", "SECRET_KEY"),
    )
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, validation_alias="JWT_EXPIRATION_HOURS")
    user_service_grpc_url: str = Field(default="localhost:50051", validation_alias="USER_SERVICE_GRPC_URL")
    processing_service_grpc_url: str = Field(
        default="localhost:50052",
        validation_alias="PROCESSING_SERVICE_GRPC_URL",
    )

    @model_validator(mode="after")
    def validate_non_dev_settings(self):
        if self.environment.lower() in DEV_ENVIRONMENTS:
            return self

        if self.user_database_url == DEV_USER_DATABASE_URL:
            raise ValueError("USER_DATABASE_URL must be set outside development")
        if self.jwt_secret == DEV_JWT_SECRET:
            raise ValueError("JWT_SECRET must be set outside development")
        if self.user_service_grpc_url.startswith("localhost"):
            raise ValueError("USER_SERVICE_GRPC_URL must not point to localhost outside development")
        if self.processing_service_grpc_url.startswith("localhost"):
            raise ValueError("PROCESSING_SERVICE_GRPC_URL must not point to localhost outside development")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

USER_DATABASE_URL = settings.user_database_url
JWT_SECRET = settings.jwt_secret
JWT_ALGORITHM = settings.jwt_algorithm
JWT_EXPIRATION_HOURS = settings.jwt_expiration_hours
USER_SERVICE_GRPC_URL = settings.user_service_grpc_url
PROCESSING_SERVICE_GRPC_URL = settings.processing_service_grpc_url
