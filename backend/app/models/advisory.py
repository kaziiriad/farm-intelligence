"""Advisory ORM model — persisted weather advisory per farm."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Advisory(Base):
    __tablename__ = "advisories"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    farm_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    # Raw weather snapshot stored as JSON
    weather_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    # Advisory scores per day (output of advisory_engine.generate_advisory)
    daily_scores: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    # Top-level recommendations (output of generate_recommendations)
    recommendations: Mapped[dict] = mapped_column(JSON, nullable=False)
    # Whether this response was served from cache
    cached: Mapped[bool] = mapped_column(default=False, nullable=False)