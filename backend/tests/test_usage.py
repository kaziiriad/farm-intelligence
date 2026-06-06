"""Usage endpoint tests."""
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import pytest


pytestmark = pytest.mark.asyncio


async def test_usage_aggregates_three_quotas(client):
    """GET /api/v1/weather-ai/usage returns api, ai, trees families from WeatherAI."""
    mock_usage_response = {
        "data": {
            "api_requests": {"used": 50, "limit": 1000},
            "ai_requests": {"used": 5, "limit": 200},
            "tree_analyses": {"used": 1, "limit": 5},
        }
    }
    mock_trees_response = {"remaining": 3, "limit": 5, "used": 2}

    with patch("app.routers.usage.WeatherClient") as MockWC:
        mock_wc = MagicMock()
        mock_wc.get_usage = AsyncMock(return_value=mock_usage_response)
        mock_wc.get_trees_quota = AsyncMock(return_value=mock_trees_response)
        MockWC.return_value = mock_wc

        resp = await client.get("/api/v1/weather-ai/usage")

    assert resp.status_code == 200
    body = resp.json()
    assert body["api"]["used"] == 50
    assert body["api"]["limit"] == 1000
    assert body["api"]["remaining"] == 950
    assert body["ai"]["used"] == 5
    assert body["ai"]["limit"] == 200
    assert body["ai"]["remaining"] == 195
    assert body["trees"]["remaining"] == 3
    assert body["trees"]["limit"] == 5
    assert body["trees"]["used"] == 2
    # remaining=3, limit=5 → 3/5=0.6 > 0.3 → healthy
    assert body["quota_status"] == "healthy"


async def test_quota_status_bands_healthy_low_critical(client):
    """quota_status band: healthy (>30%), low (>10%), critical (≤10%)."""
    test_cases = [
        # (trees_remaining, trees_limit, expected_status)
        (3, 5, "healthy"),    # 60% > 30% → healthy
        (2, 5, "healthy"),    # 40% > 30% → healthy
        (2, 10, "low"),       # 20% ≤ 30% but > 10% → low
        (1, 10, "critical"),  # 10% ≤ 10% → critical
        (0, 5, "critical"),   # 0% ≤ 10% → critical
        (1, 5, "low"),        # 20% ≤ 30% but > 10% → low
    ]
    for remaining, limit, expected_status in test_cases:
        mock_usage_response = {
            "data": {
                "api_requests": {"used": 0, "limit": 100},
                "ai_requests": {"used": 0, "limit": 100},
                "tree_analyses": {"used": 0, "limit": 5},
            }
        }
        mock_trees_response = {"remaining": remaining, "limit": limit, "used": 0}

        with patch("app.routers.usage.WeatherClient") as MockWC:
            mock_wc = MagicMock()
            mock_wc.get_usage = AsyncMock(return_value=mock_usage_response)
            mock_wc.get_trees_quota = AsyncMock(return_value=mock_trees_response)
            MockWC.return_value = mock_wc

            resp = await client.get("/api/v1/weather-ai/usage")

        assert resp.status_code == 200
        body = resp.json()
        assert body["quota_status"] == expected_status, \
            f"remaining={remaining}, limit={limit} → expected {expected_status}, got {body['quota_status']}"


async def test_usage_502_on_upstream_failure(client):
    """WeatherAI failure returns 502."""
    with patch("app.routers.usage.WeatherClient") as MockWC:
        mock_wc = MagicMock()
        mock_wc.get_usage = AsyncMock(side_effect=Exception("upstream down"))
        mock_wc.get_trees_quota = AsyncMock(side_effect=Exception("upstream down"))
        MockWC.return_value = mock_wc

        resp = await client.get("/api/v1/weather-ai/usage")

    assert resp.status_code == 502