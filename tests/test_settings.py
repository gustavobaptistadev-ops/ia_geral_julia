from app.core.config import Settings


def test_settings_loads_default_values() -> None:
    settings = Settings()

    assert settings.app_name == "LifelineOne IA"
    assert settings.environment == "development"
