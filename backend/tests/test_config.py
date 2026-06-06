"""Settings load from env via pydantic-settings."""
import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.database import build_engine_config


def test_settings_loads_defaults_when_no_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("WEATHERAI_API_KEY", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.delenv("ALLOWED_HOSTS", raising=False)
    settings = Settings(_env_file=None)
    assert settings.weatherai_base_url == "https://api.weather-ai.co"
    assert settings.cache_backend == "redis"
    assert settings.tree_image_max_mb == 20
    assert settings.allowed_host_list == ["localhost", "127.0.0.1", "test", "testserver"]


def test_settings_requires_weatherai_api_key_in_production(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("WEATHERAI_API_KEY", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_requires_allowed_hosts_in_production(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("WEATHERAI_API_KEY", "test-key-abc")
    monkeypatch.delenv("ALLOWED_HOSTS", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_reads_allowed_hosts_from_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ALLOWED_HOSTS", "api.example.com, localhost")
    settings = Settings(_env_file=None)
    assert settings.allowed_host_list == ["api.example.com", "localhost"]


def test_settings_reads_weatherai_api_key_from_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("WEATHERAI_API_KEY", "test-key-abc")
    settings = Settings(_env_file=None)
    assert settings.weatherai_api_key.get_secret_value() == "test-key-abc"


def test_postgres_url_is_normalized_for_asyncpg():
    database_url, connect_args = build_engine_config(
        "postgresql://user:pass@example.supabase.co:5432/postgres?sslmode=require"
    )
    assert database_url == "postgresql+asyncpg://user:pass@example.supabase.co:5432/postgres"
    assert connect_args == {"ssl": True}
