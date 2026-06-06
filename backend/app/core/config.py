"""Application settings loaded from environment via pydantic-settings."""
import os
from functools import lru_cache

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from dotenv import load_dotenv

# Load .env file for local dev. In Docker, env vars are injected by compose.
# Skip if DOTENV_LOAD=0 (used in tests to avoid picking up stale values).
if os.environ.get("DOTENV_LOAD", "1") == "1":
    load_dotenv()


class Settings(BaseSettings):
    """All runtime config. Values come from environment variables."""

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
    )

    # WeatherAI upstream
    weatherai_api_key: SecretStr | None = os.environ.get("WEATHERAI_API_KEY") or None
    weatherai_base_url: str = os.environ.get("WEATHERAI_BASE_URL", "https://api.weather-ai.co")
    weatherai_timeout_s: float = float(os.environ.get("WEATHERAI_TIMEOUT_S", "10.0"))
    weatherai_rate_limit_warn: int = int(os.environ.get("WEATHERAI_RATE_LIMIT_WARN", "100"))

    # App
    app_env: str = os.environ.get("APP_ENV", "development")
    log_level: str = os.environ.get("LOG_LEVEL", "info")

    # Database
    database_url: str = os.environ.get(
        "DATABASE_URL", "sqlite+aiosqlite:///./data/app.db"
    )

    # Cache
    cache_backend: str = os.environ.get("CACHE_BACKEND", "redis")
    redis_url: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    # Quota / limits
    tree_image_max_mb: int = int(os.environ.get("TREE_IMAGE_MAX_MB", "20"))
    tree_quota_limit: int = int(os.environ.get("TREE_QUOTA_LIMIT", "5"))

    # AI / OpenAI
    openai_api_key: SecretStr | None = os.environ.get("OPENAI_API_KEY") or None
    openai_base_url: str = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

    # CORS — comma-separated list of allowed origins for the frontend
    cors_allowed_origins: str = os.environ.get(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8080,http://127.0.0.1:8080,http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173",
    )
    # Trusted hosts — comma-separated HTTP Host values accepted by the API.
    allowed_hosts: str = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1,test,testserver")

    @property
    def cors_allowed_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    @property
    def allowed_host_list(self) -> list[str]:
        return [h.strip() for h in self.allowed_hosts.split(",") if h.strip()]

    @model_validator(mode="after")
    def _production_requires_key(self) -> "Settings":
        if self.app_env == "production" and not self.weatherai_api_key:
            raise ValueError("WEATHERAI_API_KEY is required when APP_ENV=production")
        if self.app_env == "production" and not os.environ.get("ALLOWED_HOSTS"):
            raise ValueError("ALLOWED_HOSTS is required when APP_ENV=production")
        return self


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — safe to call repeatedly in deps."""
    return Settings()
