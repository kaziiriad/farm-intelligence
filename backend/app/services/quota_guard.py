"""Quota guard — tracks monthly API usage per farm, enforces free-tier limit."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.quota import QuotaRecord


class QuotaExceeded(Exception):
    """Raised when farm exceeds monthly quota."""


class QuotaGuard:
    """Check-and-increment quota per farm per month."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._settings = get_settings()

    def _current_month(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m")

    async def check_and_increment(self, farm_id: uuid.UUID) -> bool:
        """Return True if within limit and increment. False if quota exceeded."""
        month = self._current_month()
        limit = self._settings.tree_quota_limit

        record = await self._db.get(QuotaRecord, (farm_id, month))

        if record is None:
            # First request this month
            new_record = QuotaRecord(
                farm_id=farm_id,
                month_year=month,
                request_count=1,
                last_incremented_at=datetime.now(timezone.utc),
            )
            self._db.add(new_record)
            await self._db.flush()
            return True

        if record.request_count >= limit:
            return False

        record.request_count += 1
        record.last_incremented_at = datetime.now(timezone.utc)
        await self._db.flush()
        return True

    async def get_remaining(self, farm_id: uuid.UUID) -> int:
        """Return remaining quota for current month."""
        month = self._current_month()
        limit = self._settings.tree_quota_limit

        record = await self._db.get(QuotaRecord, (farm_id, month))
        if record is None:
            return limit

        return max(0, limit - record.request_count)