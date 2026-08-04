from app.core.config import Settings


def test_settings_loads_default_values() -> None:
    settings = Settings()

    assert settings.app_name == "LifelineOne IA"
    assert settings.environment == "development"
    assert settings.enable_postgres_persistence is False


def test_settings_loads_google_and_security_defaults() -> None:
    settings = Settings()

    assert settings.google_calendar_scope == "https://www.googleapis.com/auth/calendar"
    assert settings.api_secret_key == "dev-secret-key"
    assert settings.allowed_origins == "http://localhost:3000"
