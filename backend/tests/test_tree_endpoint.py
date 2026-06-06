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
        "health_status": "healthy",
        "confidence": 0.92,
        "issues": [],
    }

    with patch("app.routers.trees.QuotaGuard") as MockQuotaGuard:
        mock_guard_instance = AsyncMock()
        mock_guard_instance.check_and_increment.return_value = True
        mock_guard_instance.get_remaining.return_value = 99
        MockQuotaGuard.return_value = mock_guard_instance

        with patch("app.routers.trees.TreeAnalysisClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.analyze_tree_image = AsyncMock(return_value=mock_analysis_result)
            MockClient.return_value = mock_client_instance

            # Send fake image data
            resp = await client.post(
                f"/api/v1/farms/{farm_id}/tree-analysis",
                files={"image": ("tree.jpg", b"fake-image-data", "image/jpeg")},
            )

    assert resp.status_code == 200
    body = resp.json()
    assert body["farm_id"] == farm_id
    assert body["analysis_result"]["health_status"] == "healthy"
    assert body["quota_remaining"] == 99  # 100 - 1


async def test_tree_analysis_quota_exceeded_returns_429(client):
    """Quota exceeded returns 429."""
    farm_payload = {
        "farmer_name": "Quota Farmer",
        "county": "Nairobi",
        "crop_type": "tea",
        "latitude": -1.0,
        "longitude": 37.0,
    }
    farm_resp = await client.post("/api/v1/farms", json=farm_payload)
    farm_id = farm_resp.json()["id"]

    with patch("app.routers.trees.QuotaGuard") as MockQuotaGuard:
        mock_guard_instance = AsyncMock()
        mock_guard_instance.check_and_increment.return_value = False
        mock_guard_instance.get_remaining.return_value = 0
        MockQuotaGuard.return_value = mock_guard_instance

        resp = await client.post(
            f"/api/v1/farms/{farm_id}/tree-analysis",
            files={"image": ("tree.jpg", b"fake-image-data", "image/jpeg")},
        )

    assert resp.status_code == 429


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

    mock_analysis_result = {"health_status": "healthy", "confidence": 0.92, "issues": []}

    with patch("app.routers.trees.QuotaGuard") as MockQG:
        mock_qg = AsyncMock()
        mock_qg.check_and_increment.return_value = True
        mock_qg.get_remaining.return_value = 99
        MockQG.return_value = mock_qg

        with patch("app.routers.trees.TreeAnalysisClient") as MockTC:
            mock_tc = AsyncMock()
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
    assert record.analysis_result["health_status"] == "healthy"


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
        mock_qg = AsyncMock()
        mock_qg.check_and_increment.return_value = True
        mock_qg.get_remaining.return_value = 99
        MockQG.return_value = mock_qg

        with patch("app.routers.trees.TreeAnalysisClient") as MockTC:
            mock_tc = AsyncMock()
            mock_tc.analyze_tree_image = AsyncMock(side_effect=Exception("AI unavailable"))
            MockTC.return_value = mock_tc

            resp = await client.post(
                f"/api/v1/farms/{farm_id}/tree-analysis",
                files={"image": ("tree.jpg", b"fake-image-data", "image/jpeg")},
            )

    assert resp.status_code == 502


async def test_quota_endpoint_returns_usage(client, db_session):
    """GET /api/v1/farms/{id}/quota returns limit/used/remaining."""
    farm_payload = {
        "farmer_name": "Quota Check Farmer",
        "county": "Nairobi",
        "crop_type": "tea",
        "latitude": -1.0,
        "longitude": 37.0,
    }
    farm_resp = await client.post("/api/v1/farms", json=farm_payload)
    farm_id = farm_resp.json()["id"]

    # Pre-populate quota record
    from app.models.quota import QuotaRecord
    from datetime import datetime, timezone
    record = QuotaRecord(
        farm_id=uuid.UUID(farm_id),
        month_year="2026-06",
        request_count=45,
        last_incremented_at=datetime.now(timezone.utc),
    )
    db_session.add(record)
    await db_session.commit()

    resp = await client.get(f"/api/v1/farms/{farm_id}/quota")

    assert resp.status_code == 200
    body = resp.json()
    assert body["limit"] == 100
    assert body["used"] == 45
    assert body["remaining"] == 55


async def test_quota_404_unknown_farm(client):
    """GET /api/v1/farms/{id}/quota returns 404 for unknown farm."""
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/farms/{fake_id}/quota")
    assert resp.status_code == 404


async def test_tree_analysis_image_too_large_returns_413(client):
    """Image exceeding size limit returns 413."""
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
        mock_qg = AsyncMock()
        mock_qg.check_and_increment.return_value = True
        mock_qg.get_remaining.return_value = 99
        MockQG.return_value = mock_qg

        with patch("app.routers.trees.get_settings") as mock_settings:
            s = MagicMock()
            s.tree_image_max_mb = 0  # effectively 0 bytes
            s.openai_api_key = MagicMock()
            s.openai_api_key.get_secret_value.return_value = ""
            s.openai_base_url = "https://api.openai.com/v1"
            mock_settings.return_value = s

            # Send 100 bytes (exceeds 0 MB limit)
            resp = await client.post(
                f"/api/v1/farms/{farm_id}/tree-analysis",
                files={"image": ("tree.jpg", b"x" * 100, "image/jpeg")},
            )

    assert resp.status_code == 413