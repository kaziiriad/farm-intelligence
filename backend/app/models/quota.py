"""Quota record ORM model — tracks monthly API usage per farm."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class QuotaRecord(Base):
    """Monthly request count per farm. Primary key is (farm_id, month_year)."""

    __tablename__ = "quota_records"
    __table_args__ = (
        UniqueConstraint("farm_id", "month_year", name="uq_quota_farm_month"),
    )

    farm_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    month_year: Mapped[str] = mapped_column(String(7), primary_key=True)  # "YYYY-MM"
    request_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_incremented_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )