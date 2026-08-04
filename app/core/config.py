import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "LifelineOne IA")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    postgres_url: str = os.getenv("POSTGRES_URL", "postgresql://postgres:postgres@localhost:5432/lifelineone")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    google_calendar_api_key: str | None = os.getenv("GOOGLE_CALENDAR_API_KEY")
    google_calendar_scope: str = os.getenv("GOOGLE_CALENDAR_SCOPE", "https://www.googleapis.com/auth/calendar")
    api_secret_key: str = os.getenv("API_SECRET_KEY", "dev-secret-key")
    allowed_origins: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")


settings = Settings()
