"""Usage endpoint tests."""
import uuid

import pytest


pytestmark = pytest.mark.asyncio


async def test_usage_returns_counts(client):
    """GET /api/v1/usage returns total farms, advisories, tree analyses."""
    # Create a farm first
    farm_payload = {
        "farmer_name": "Usage Farmer",
        "county": "Nairobi",
        "crop_type": "tea",
        "latitude": -1.0,
        "longitude": 37.0,
    }
    await client.post("/api/v1/farms", json=farm_payload)

    resp = await client.get("/api/v1/usage")

    assert resp.status_code == 200
    body = resp.json()
    assert body["total_farms"] >= 1
    assert body["total_advisories"] == 0
    assert body["total_tree_analyses"] == 0
    assert body["quota_limit_per_farm"] == 100