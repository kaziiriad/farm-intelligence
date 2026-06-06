"""Tree analysis endpoint tests."""
from unittest.mock import AsyncMock, patch, MagicMock
import uuid

import pytest


pytestmark = pytest.mark.asyncio


async def test_tree_analysis_returns_result(client):
    """POST /api/v1/farms/{id}/tree-analysis returns analysis + quota_remaining."""
    farm_payload = {
        "farmer_name": "Tree Farmer",
        "county": "Nairobi",
        "crop_type": "tea",
        "latitude": -1.0,
        "longitude": 37.0,
    }
    farm_resp = await client.post("/api/v1/farms", json=farm_payload)
    farm_id = farm_resp.json()["id"]

    mock_analysis_result = {
        "tree_count": 42,
        "canopy_health": "good",
        "observations": [],
    }

    with patch("app.routers.trees.QuotaGuard") as MockQG:
        mock_qg = MagicMock()
        mock_qg.check = AsyncMock(return_value=(True, 4))
        mock_qg.get_quota = AsyncMock(return_value={"remaining": 4, "limit": 5, "used": 1})
        MockQG.return_value = mock_qg

        with patch("app.routers.trees.TreeAnalysisClient") as MockTC:
            mock_tc = MagicMock()
            mock_tc.analyze_tree_image = AsyncMock(return_value=mock_analysis_result)
            MockTC.return_value = mock_tc

            resp = await client.post(
                f"/api/v1/farms/{farm_id}/tree-analysis",
                files={"image": ("tree.jpg", b"fake-image-data", "image/jpeg")},
            )

    assert resp.status_code == 200
    body = resp.json()
    assert body["farm_id"] == farm_id
    assert body["analysis_result"]["tree_count"] == 42
    assert body["quota_remaining"] == 4


async def test_tree_analysis_quota_exceeded_returns_429(client):
    """Quota exceeded returns 429 before image is sent to WeatherAI."""
    farm_payload = {
        "farmer_name": "Quota Farmer",
        "county": "Nairobi",
        "crop_type": "tea",
        "latitude": -1.0,
        "longitude": 37.0,
    }
    farm_resp = await client.post("/api/v1/farms", json=farm_payload)
    farm_id = farm_resp.json()["id"]

    with patch("app.routers.trees.QuotaGuard") as MockQG:
        mock_qg = MagicMock()
        mock_qg.check = AsyncMock(return_value=(False, 0))
        MockQG.return_value = mock_qg

        with patch("app.routers.trees.TreeAnalysisClient") as MockTC:
            mock_tc = MagicMock()
            mock_tc.analyze_tree_image = AsyncMock()  # should NOT be called
            MockTC.return_value = mock_tc

            resp = await client.post(
                f"/api/v1/farms/{farm_id}/tree-analysis",
                files={"image": ("tree.jpg", b"fake-image-data", "image/jpeg")},
            )

    assert resp.status_code == 429
    # TreeAnalysisClient should not have been called
    mock_tc.analyze_tree_image.assert_not_called()


async def test_tree_analysis_404_unknown_farm(client):
    """Unknown farm returns 404."""
    fake_id = str(uuid.uuid4())
    resp = await client.post(
        f"/api/v1/farms/{fake_id}/tree-analysis",
        files={"image": ("tree.jpg", b"fake-image-data", "image/jpeg")},
    )
    assert resp.status_code == 404


async def test_tree_analysis_persisted_to_database(client, db_session):
    """Tree analysis is stored in tree_analyses table."""
    farm_payload = {
        "farmer_name": "Persist Tree Farmer",
        "county": "Nairobi",
        "crop_type": "tea",
        "latitude": -1.0,
        "longitude": 37.0,
    }
    farm_resp = await client.post("/api/v1/farms", json=farm_payload)
    farm_id = farm_resp.json()["id"]

    mock_analysis_result = {"tree_count": 10, "canopy_health": "fair", "observations": []}

    with patch("app.routers.trees.QuotaGuard") as MockQG:
        mock_qg = MagicMock()
        mock_qg.check = AsyncMock(return_value=(True, 9))
        MockQG.return_value = mock_qg

        with patch("app.routers.trees.TreeAnalysisClient") as MockTC:
            mock_tc = MagicMock()
            mock_tc.analyze_tree_image = AsyncMock(return_value=mock_analysis_result)
            MockTC.return_value = mock_tc

            resp = await client.post(
                f"/api/v1/farms/{farm_id}/tree-analysis",
                files={"image": ("tree.jpg", b"fake-image-data", "image/jpeg")},
            )

    assert resp.status_code == 200
    analysis_id = resp.json()["id"]

    from app.models.tree_analysis import TreeAnalysis
    record = await db_session.get(TreeAnalysis, uuid.UUID(analysis_id))
    assert record is not None
    assert str(record.farm_id) == farm_id
    assert record.analysis_result["tree_count"] == 10


async def test_tree_analysis_ai_failure_returns_502(client):
    """AI service failure returns 502."""
    farm_payload = {
        "farmer_name": "AI Fail Farmer",
        "county": "Nairobi",
        "crop_type": "tea",
        "latitude": -1.0,
        "longitude": 37.0,
    }
    farm_resp = await client.post("/api/v1/farms", json=farm_payload)
    farm_id = farm_resp.json()["id"]

    with patch("app.routers.trees.QuotaGuard") as MockQG:
        mock_qg = MagicMock()
        mock_qg.check = AsyncMock(return_value=(True, 9))
        MockQG.return_value = mock_qg

        with patch("app.routers.trees.TreeAnalysisClient") as MockTC:
            mock_tc = MagicMock()
            mock_tc.analyze_tree_image = AsyncMock(side_effect=Exception("AI unavailable"))
            MockTC.return_value = mock_tc

            resp = await client.post(
                f"/api/v1/farms/{farm_id}/tree-analysis",
                files={"image": ("tree.jpg", b"fake-image-data", "image/jpeg")},
            )

    assert resp.status_code == 502


async def test_quota_endpoint_returns_usage(client, db_session):
    """GET /api/v1/farms/{id}/quota returns limit/used/remaining from WeatherAI."""
    farm_payload = {
        "farmer_name": "Quota Check Farmer",
        "county": "Nairobi",
        "crop_type": "tea",
        "latitude": -1.0,
        "longitude": 37.0,
    }
    farm_resp = await client.post("/api/v1/farms", json=farm_payload)
    farm_id = farm_resp.json()["id"]

    with patch("app.routers.trees.QuotaGuard") as MockQG:
        mock_qg = MagicMock()
        mock_qg.get_quota = AsyncMock(return_value={"remaining": 3, "limit": 5, "used": 2})
        MockQG.return_value = mock_qg

        resp = await client.get(f"/api/v1/farms/{farm_id}/quota")

    assert resp.status_code == 200
    body = resp.json()
    assert body["limit"] == 5
    assert body["used"] == 2
    assert body["remaining"] == 3


async def test_quota_404_unknown_farm(client):
    """GET /api/v1/farms/{id}/quota returns 404 for unknown farm."""
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/farms/{fake_id}/quota")
    assert resp.status_code == 404


async def test_tree_analysis_image_too_large_returns_413(client):
    """Image exceeding size limit returns 413 before any upstream calls."""
    farm_payload = {
        "farmer_name": "Large Image Farmer",
        "county": "Nairobi",
        "crop_type": "tea",
        "latitude": -1.0,
        "longitude": 37.0,
    }
    farm_resp = await client.post("/api/v1/farms", json=farm_payload)
    farm_id = farm_resp.json()["id"]

    with patch("app.routers.trees.QuotaGuard") as MockQG:
        mock_qg = MagicMock()
        mock_qg.check = AsyncMock()  # should NOT be called
        MockQG.return_value = mock_qg

        with patch("app.routers.trees.get_settings") as mock_settings:
            s = MagicMock()
            s.tree_image_max_mb = 0  # effectively 0 bytes
            mock_settings.return_value = s

            resp = await client.post(
                f"/api/v1/farms/{farm_id}/tree-analysis",
                files={"image": ("tree.jpg", b"x" * 100, "image/jpeg")},
            )

    assert resp.status_code == 413
    # QuotaGuard.check should NOT have been called
    mock_qg.check.assert_not_called()


async def test_list_tree_analyses_pagination(client, db_session):
    """GET /api/v1/farms/{id}/tree-analyses returns paginated history."""
    farm_payload = {
        "farmer_name": "History Tree Farmer",
        "county": "Nairobi",
        "crop_type": "tea",
        "latitude": -1.0,
        "longitude": 37.0,
    }
    farm_resp = await client.post("/api/v1/farms", json=farm_payload)
    farm_id = farm_resp.json()["id"]

    mock_analysis_result = {"tree_count": 5, "canopy_health": "good", "observations": []}

    with patch("app.routers.trees.QuotaGuard") as MockQG:
        mock_qg = MagicMock()
        mock_qg.check = AsyncMock(return_value=(True, 97))
        MockQG.return_value = mock_qg

        with patch("app.routers.trees.TreeAnalysisClient") as MockTC:
            mock_tc = MagicMock()
            mock_tc.analyze_tree_image = AsyncMock(return_value=mock_analysis_result)
            MockTC.return_value = mock_tc

            # Create 3 tree analyses
            for _ in range(3):
                await client.post(
                    f"/api/v1/farms/{farm_id}/tree-analysis",
                    files={"image": ("tree.jpg", b"fake", "image/jpeg")},
                )

    # Paginate
    resp = await client.get(f"/api/v1/farms/{farm_id}/tree-analyses?limit=2&offset=0")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 2
    assert body["total"] == 3


async def test_list_tree_analyses_404_unknown_farm(client):
    """Unknown farm returns 404."""
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/farms/{fake_id}/tree-analyses")
    assert resp.status_code == 404


async def test_tree_analysis_with_weather_returns_both(client):
    """POST with with_weather=true returns analysis_result + weather data."""
    farm_payload = {
        "farmer_name": "Weather Tree Farmer",
        "county": "Nairobi",
        "crop_type": "tea",
        "latitude": -1.0,
        "longitude": 37.0,
    }
    farm_resp = await client.post("/api/v1/farms", json=farm_payload)
    farm_id = farm_resp.json()["id"]

    mock_analysis_result = {"tree_count": 42, "canopy_health": "good", "observations": []}
    mock_weather = {"current": {"temp": 22, "humidity": 65}, "meta": {"cached": False}}

    with patch("app.routers.trees.QuotaGuard") as MockQG:
        mock_qg = MagicMock()
        mock_qg.check = AsyncMock(return_value=(True, 4))
        MockQG.return_value = mock_qg

        with patch("app.routers.trees.TreeAnalysisClient") as MockTC:
            mock_tc = MagicMock()
            mock_tc.analyze_tree_image = AsyncMock(return_value=mock_analysis_result)
            MockTC.return_value = mock_tc

            with patch("app.routers.trees.WeatherClient") as MockWC:
                mock_wc = MagicMock()
                mock_wc.get_current = AsyncMock(return_value=mock_weather)
                MockWC.return_value = mock_wc

                resp = await client.post(
                    f"/api/v1/farms/{farm_id}/tree-analysis?with_weather=true",
                    files={"image": ("tree.jpg", b"fake-image-data", "image/jpeg")},
                )

    assert resp.status_code == 200
    body = resp.json()
    assert body["analysis_result"]["tree_count"] == 42
    assert body["weather"] is not None
    assert body["weather"]["current"]["temp"] == 22


async def test_partial_success_when_weather_fails(client):
    """Weather failure with with_weather=true returns tree result + weather=null (no 502)."""
    farm_payload = {
        "farmer_name": "Weather Fail Farmer",
        "county": "Nairobi",
        "crop_type": "tea",
        "latitude": -1.0,
        "longitude": 37.0,
    }
    farm_resp = await client.post("/api/v1/farms", json=farm_payload)
    farm_id = farm_resp.json()["id"]

    mock_analysis_result = {"tree_count": 42, "canopy_health": "good", "observations": []}

    with patch("app.routers.trees.QuotaGuard") as MockQG:
        mock_qg = MagicMock()
        mock_qg.check = AsyncMock(return_value=(True, 4))
        MockQG.return_value = mock_qg

        with patch("app.routers.trees.TreeAnalysisClient") as MockTC:
            mock_tc = MagicMock()
            mock_tc.analyze_tree_image = AsyncMock(return_value=mock_analysis_result)
            MockTC.return_value = mock_tc

            with patch("app.routers.trees.WeatherClient") as MockWC:
                mock_wc = MagicMock()
                # Weather fails
                mock_wc.get_current = AsyncMock(side_effect=Exception("weather down"))
                MockWC.return_value = mock_wc

                resp = await client.post(
                    f"/api/v1/farms/{farm_id}/tree-analysis?with_weather=true",
                    files={"image": ("tree.jpg", b"fake-image-data", "image/jpeg")},
                )

    # Tree analysis should still succeed; weather=null
    assert resp.status_code == 200
    body = resp.json()
    assert body["analysis_result"]["tree_count"] == 42
    assert body["weather"] is None