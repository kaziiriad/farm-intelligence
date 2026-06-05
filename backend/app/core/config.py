"""Application settings loaded from environment via pydantic-settings."""
from functools import lru_cache

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime config. Values come from env vars (or .env in dev)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # WeatherAI upstream
    weatherai_api_key: SecretStr | None = None
    weatherai_base_url: str = "https://api.weather-ai.co"
    weatherai_timeout_s: float = 10.0
    weatherai_rate_limit_warn: int = 100

    # App
    app_env: str = "development"
    log_level: str = "info"

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/app.db"

    # Cache
    cache_backend: str = "redis"  # "redis" or "memory"
    redis_url: str = "redis://localhost:6379/0"

    # Quota / limits
    tree_image_max_mb: int = 20

    @model_validator(mode="after")
    def _production_requires_key(self) -> "Settings":
        if self.app_env == "production" and not self.weatherai_api_key:
            raise ValueError("WEATHERAI_API_KEY is required when APP_ENV=production")
        return self


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — safe to call repeatedly in deps."""
    return Settings()