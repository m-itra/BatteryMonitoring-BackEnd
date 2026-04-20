from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
REPOSITORY_DIR = PROJECT_DIR.parent
ENV_PATH = REPOSITORY_DIR / "Infrastructure" / ".env"
DEV_JWT_SECRET = "dev-secret-change-me"
DEV_ENVIRONMENTS = {"development", "dev", "local", "test"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = Field(default="development", validation_alias=AliasChoices("ENVIRONMENT", "APP_ENV"))
    jwt_secret: str = Field(
        default=DEV_JWT_SECRET,
        validation_alias=AliasChoices("JWT_SECRET", "SECRET_KEY"),
    )
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    auth_cookie_secure: bool = Field(default=False, validation_alias="AUTH_COOKIE_SECURE")
    auth_cookie_samesite: str = Field(default="lax", validation_alias="AUTH_COOKIE_SAMESITE")
    auth_cookie_max_age_seconds: int = Field(default=24 * 60 * 60, validation_alias="AUTH_COOKIE_MAX_AGE_SECONDS")
    user_service_url: str = Field(default="http://localhost:8001", validation_alias="USER_SERVICE_URL")
    processing_service_url: str = Field(
        default="http://localhost:8002",
        validation_alias="PROCESSING_SERVICE_URL",
    )
    analytics_service_url: str = Field(
        default="http://localhost:8003",
        validation_alias="ANALYTICS_SERVICE_URL",
    )

    @model_validator(mode="after")
    def validate_non_dev_settings(self):
        if self.environment.lower() in DEV_ENVIRONMENTS:
            return self

        if self.jwt_secret == DEV_JWT_SECRET:
            raise ValueError("JWT_SECRET must be set outside development")
        if "localhost" in self.user_service_url:
            raise ValueError("USER_SERVICE_URL must not point to localhost outside development")
        if "localhost" in self.processing_service_url:
            raise ValueError("PROCESSING_SERVICE_URL must not point to localhost outside development")
        if "localhost" in self.analytics_service_url:
            raise ValueError("ANALYTICS_SERVICE_URL must not point to localhost outside development")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

JWT_SECRET = settings.jwt_secret
JWT_ALGORITHM = settings.jwt_algorithm
AUTH_COOKIE_SECURE = settings.auth_cookie_secure
AUTH_COOKIE_SAMESITE = settings.auth_cookie_samesite
AUTH_COOKIE_MAX_AGE_SECONDS = settings.auth_cookie_max_age_seconds
USER_SERVICE_URL = settings.user_service_url
PROCESSING_SERVICE_URL = settings.processing_service_url
ANALYTICS_SERVICE_URL = settings.analytics_service_url
