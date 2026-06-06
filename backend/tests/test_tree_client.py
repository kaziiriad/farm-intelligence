"""Tree analysis client and quota guard tests."""
from unittest.mock import AsyncMock, patch, MagicMock
import uuid

import pytest

from app.services.tree_client import TreeAnalysisClient, TreeAnalysisError
from app.services.quota_guard import QuotaGuard
from app.core.config import get_settings


pytestmark = pytest.mark.asyncio


class TestTreeAnalysisClient:
    """Tests for TreeAnalysisClient."""

    async def test_analyze_returns_result(self):
        """Successful analysis returns parsed result."""
        mock_http = AsyncMock()
        mock_cache = MagicMock()

        with patch("app.services.tree_client.get_settings") as mock_settings:
            s = MagicMock()
            s.openai_api_key = MagicMock()
            s.openai_api_key.get_secret_value.return_value = "test-key"
            s.openai_base_url = "https://api.openai.com/v1"
            s.tree_image_max_mb = 20
            mock_settings.return_value = s

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = ""
            mock_response.json.return_value = {
                "choices": [{"message": {"content": '{"health_status":"healthy","confidence":0.92}'}}]
            }
            mock_http.post.return_value = mock_response

            client = TreeAnalysisClient(mock_http, mock_cache, "https://api.openai.com/v1", "test-key")
            result = await client.analyze_tree_image(b"fake-image-data", "image/png")

        assert result["health_status"] == "healthy"
        assert result["confidence"] == 0.92

    async def test_analyze_raises_on_api_error(self):
        """OpenAI API error raises TreeAnalysisError."""
        mock_http = AsyncMock()
        mock_cache = MagicMock()

        with patch("app.services.tree_client.get_settings") as mock_settings:
            s = MagicMock()
            s.openai_api_key = MagicMock()
            s.openai_api_key.get_secret_value.return_value = "test-key"
            s.openai_base_url = "https://api.openai.com/v1"
            s.tree_image_max_mb = 20
            mock_settings.return_value = s

            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.text = "Rate limit exceeded"
            mock_response.json.return_value = {}
            mock_http.post.return_value = mock_response

            client = TreeAnalysisClient(mock_http, mock_cache, "https://api.openai.com/v1", "test-key")

            with pytest.raises(TreeAnalysisError):
                await client.analyze_tree_image(b"fake-image-data", "image/png")


class TestQuotaGuard:
    """Tests for QuotaGuard."""

    async def test_check_quota_within_limit(self, db_session):
        """Farm under quota limit returns True and increments."""
        guard = QuotaGuard(db_session)
        farm_id = uuid.uuid4()

        result = await guard.check_and_increment(farm_id)

        assert result is True
        from app.models.quota import QuotaRecord
        record = await db_session.get(QuotaRecord, (farm_id, "2026-06"))
        assert record is not None
        assert record.request_count == 1

    async def test_check_quota_blocks_when_limit_reached(self, db_session):
        """Farm at quota limit returns False and does not increment."""
        guard = QuotaGuard(db_session)
        farm_id = uuid.uuid4()

        from app.models.quota import QuotaRecord
        from datetime import datetime, timezone
        record = QuotaRecord(
            farm_id=farm_id,
            month_year="2026-06",
            request_count=100,
            last_incremented_at=datetime.now(timezone.utc),
        )
        db_session.add(record)
        await db_session.commit()

        result = await guard.check_and_increment(farm_id)

        assert result is False
        from sqlalchemy import select
        stmt = select(QuotaRecord).where(QuotaRecord.farm_id == farm_id)
        row = (await db_session.execute(stmt)).scalar_one()
        assert row.request_count == 100

    async def test_get_remaining_returns_correct_count(self, db_session):
        """Remaining = limit - count."""
        guard = QuotaGuard(db_session)
        farm_id = uuid.uuid4()

        from app.models.quota import QuotaRecord
        from datetime import datetime, timezone
        record = QuotaRecord(
            farm_id=farm_id,
            month_year="2026-06",
            request_count=30,
            last_incremented_at=datetime.now(timezone.utc),
        )
        db_session.add(record)
        await db_session.commit()

        remaining = await guard.get_remaining(farm_id)

        assert remaining == 70