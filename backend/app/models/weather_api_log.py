"""WeatherAPI call log ORM model."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WeatherApiLog(Base):
    """Persisted log of every WeatherAI API call — endpoint, status, latency, cache_hit."""

    __tablename__ = "weather_api_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    request_params: Mapped[dict] = mapped_column(JSON, nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, index=True
    )