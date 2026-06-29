from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    database_url: str = "postgresql+asyncpg://autoapply:autoapply-dev@localhost:5432/autoapply"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    jwt_issuer: str = "autoapply-ai"
    jwt_access_secret: str = "change-me-access"
    jwt_refresh_secret: str = "change-me-refresh"
    jwt_access_ttl_seconds: int = 900
    jwt_refresh_ttl_seconds: int = 2_592_000
    password_pepper: str = "change-me-password-pepper"

    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str | None = None

    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    s3_bucket: str = "autoapply-local"
    aws_region: str = "us-east-1"
    kms_key_id: str | None = None

    max_upload_mb: int = 10

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    email_from: str = "noreply@autoapply.ai"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

