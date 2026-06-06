"""Tree analysis client and quota guard tests."""
from unittest.mock import AsyncMock, MagicMock
import uuid

import pytest

from app.services.tree_client import TreeAnalysisClient, TreeAnalysisError
from app.services.quota_guard import QuotaGuard


pytestmark = pytest.mark.asyncio


class TestTreeAnalysisClient:
    """Tests for TreeAnalysisClient."""

    async def test_analyze_returns_result(self):
        """Successful analysis returns parsed result."""
        mock_http = AsyncMock()
        mock_cache = MagicMock()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tree_count": 42,
            "canopy_health": "good",
            "observations": "healthy canopy coverage",
        }
        mock_http.get.return_value = mock_response
        mock_http.post.return_value = mock_response

        client = TreeAnalysisClient(
            mock_http,
            mock_cache,
            "https://api.weather-ai.co",
            "test-key",
        )
        result = await client.analyze_tree_image(b"fake-image-data", "image/png")

        assert result["tree_count"] == 42
        assert result["canopy_health"] == "good"
        call_kwargs = mock_http.post.call_args.kwargs
        assert "image" in call_kwargs["files"]

    async def test_analyze_raises_on_api_error(self):
        """WeatherAI API error raises TreeAnalysisError."""
        mock_http = AsyncMock()
        mock_cache = MagicMock()

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_response.json.return_value = {}
        mock_http.post.return_value = mock_response

        client = TreeAnalysisClient(
            mock_http,
            mock_cache,
            "https://api.weather-ai.co",
            "test-key",
        )

        with pytest.raises(TreeAnalysisError):
            await client.analyze_tree_image(b"fake-image-data", "image/png")


class TestQuotaGuard:
    """Tests for QuotaGuard — proxies to WeatherAI /v1/trees/quota."""

    async def test_check_returns_true_when_quota_available(self):
        """Within limit returns True with remaining count."""
        mock_http = AsyncMock()
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None  # no cache

        mock_quota_response = MagicMock()
        mock_quota_response.status_code = 200
        mock_quota_response.json.return_value = {"remaining": 4, "limit": 5, "used": 1}
        mock_http.get.return_value = mock_quota_response

        guard = QuotaGuard(mock_http, mock_cache, "https://api.weather-ai.co", "test-key")
        within_limit, remaining = await guard.check()

        assert within_limit is True
        assert remaining == 4
        # Cache should have been set
        mock_cache.set.assert_called_once()

    async def test_check_returns_false_when_quota_exhausted(self):
        """At zero remaining returns False."""
        mock_http = AsyncMock()
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None

        mock_quota_response = MagicMock()
        mock_quota_response.status_code = 200
        mock_quota_response.json.return_value = {"remaining": 0, "limit": 5, "used": 5}
        mock_http.get.return_value = mock_quota_response

        guard = QuotaGuard(mock_http, mock_cache, "https://api.weather-ai.co", "test-key")
        within_limit, remaining = await guard.check()

        assert within_limit is False
        assert remaining == 0

    async def test_check_uses_cached_quota(self):
        """Repeat calls use cached value, not upstream."""
        mock_http = AsyncMock()
        mock_cache = AsyncMock()
        mock_cache.get.return_value = '{"remaining": 3, "limit": 5, "used": 2}'

        guard = QuotaGuard(mock_http, mock_cache, "https://api.weather-ai.co", "test-key")
        within_limit, remaining = await guard.check()

        assert within_limit is True
        assert remaining == 3
        # No upstream call made
        mock_http.get.assert_not_called()

    async def test_get_quota_returns_upstream_data(self):
        """get_quota returns raw upstream data."""
        mock_http = AsyncMock()
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None

        mock_quota_response = MagicMock()
        mock_quota_response.status_code = 200
        mock_quota_response.json.return_value = {"remaining": 2, "limit": 5, "used": 3}
        mock_http.get.return_value = mock_quota_response

        guard = QuotaGuard(mock_http, mock_cache, "https://api.weather-ai.co", "test-key")
        quota = await guard.get_quota()

        assert quota["remaining"] == 2
        assert quota["limit"] == 5
        assert quota["used"] == 3