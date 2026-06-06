"""Advisory endpoint tests."""
from unittest.mock import AsyncMock, patch
import uuid

import pytest

from app.models.advisory import Advisory


pytestmark = pytest.mark.asyncio


async def test_advisory_endpoint_returns_201_and_scores(client):
    """POST /api/v1/farms/{id}/advisory returns 201 with daily scores."""
    # First create a farm
    farm_payload = {
        "farmer_name": "Test Farmer",
        "county": "Nairobi",
        "crop_type": "tea",
        "latitude": -1.0,
        "longitude": 37.0,
    }
    farm_resp = await client.post("/api/v1/farms", json=farm_payload)
    assert farm_resp.status_code == 201
    farm_id = farm_resp.json()["id"]

    # Mock weather data — matches actual WeatherAI response structure
    mock_weather = {
        "daily": [
            {
                "date": "2026-06-07",
                "precipitation_probability": 20.0,
                "temp_max": 25.0,
                "wind_max": 10.0,
            },
            {
                "date": "2026-06-08",
                "precipitation_probability": 75.0,
                "temp_max": 30.0,
                "wind_max": 16.0,
            },
        ],
        "meta": {"cached": False},
    }

    with patch(
        "app.routers.advisories.WeatherClient"
    ) as MockWeatherClient:
        instance = MockWeatherClient.return_value
        instance.get_daily = AsyncMock(return_value=mock_weather)

        resp = await client.get(f"/api/v1/farms/{farm_id}/advisory")

    assert resp.status_code == 200
    body = resp.json()
    assert body["farm_id"] == farm_id
    assert len(body["daily_scores"]) == 2
    assert body["cached"] is False
    # Day 1: all low scores
    assert body["daily_scores"][0]["risk_band"] == "low"
    # Day 2: rain (75% -> 40) + heat (30 -> 12) + wind (16 -> 10) + humidity=0 -> 62 -> medium
    assert body["daily_scores"][1]["risk_band"] == "medium"
    assert "spraying" in body["recommendations"]
    assert "irrigation" in body["recommendations"]


async def test_advisory_returns_cached_true_when_weather_cached(client):
    """When upstream returns cached:true, advisory.cached reflects that."""
    farm_payload = {
        "farmer_name": "Cached Farmer",
        "county": "Kiambu",
        "crop_type": "maize",
        "latitude": -0.5,
        "longitude": 36.5,
    }
    farm_resp = await client.post("/api/v1/farms", json=farm_payload)
    farm_id = farm_resp.json()["id"]

    mock_weather = {
        "daily": [],
        "meta": {"cached": True},
    }

    with patch("app.routers.advisories.WeatherClient") as MockWeatherClient:
        instance = MockWeatherClient.return_value
        instance.get_daily = AsyncMock(return_value=mock_weather)

        resp = await client.get(f"/api/v1/farms/{farm_id}/advisory")

    assert resp.status_code == 200
    assert resp.json()["cached"] is True


async def test_advisory_404_for_unknown_farm(client):
    """Unknown farm_id returns 404."""
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/farms/{fake_id}/advisory")
    assert resp.status_code == 404


async def test_advisory_502_when_upstream_fails(client):
    """WeatherAI error returns 502."""
    farm_payload = {
        "farmer_name": "Fail Farmer",
        "county": "Nakuru",
        "crop_type": "coffee",
        "latitude": 0.0,
        "longitude": 36.0,
    }
    farm_resp = await client.post("/api/v1/farms", json=farm_payload)
    farm_id = farm_resp.json()["id"]

    import httpx

    with patch("app.routers.advisories.WeatherClient") as MockWeatherClient:
        instance = MockWeatherClient.return_value
        instance.get_daily = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Service unavailable",
                request=httpx.Request("GET", "https://api.weather-ai.co"),
                response=httpx.Response(503),
            )
        )

        resp = await client.get(f"/api/v1/farms/{farm_id}/advisory")

    assert resp.status_code == 502


async def test_advisory_persists_to_database(client, db_session):
    """Generated advisory is stored in the advisories table."""
    farm_payload = {
        "farmer_name": "Persist Farmer",
        "county": "Bomet",
        "crop_type": "tea",
        "latitude": -0.8,
        "longitude": 35.3,
    }
    farm_resp = await client.post("/api/v1/farms", json=farm_payload)
    farm_id = farm_resp.json()["id"]

    mock_weather = {
        "daily": [{"date": "2026-06-07", "precipitation_probability": 10.0, "temp_max": 22.0, "wind_max": 5.0}],
        "meta": {"cached": False},
    }

    with patch("app.routers.advisories.WeatherClient") as MockWeatherClient:
        instance = MockWeatherClient.return_value
        instance.get_daily = AsyncMock(return_value=mock_weather)

        resp = await client.get(f"/api/v1/farms/{farm_id}/advisory")

    assert resp.status_code == 200
    advisory_id = resp.json()["id"]

    # Verify in DB
    advisory = await db_session.get(Advisory, uuid.UUID(advisory_id))
    assert advisory is not None
    assert str(advisory.farm_id) == farm_id
    assert len(advisory.daily_scores) == 1


async def test_list_advisories_pagination(client, db_session):
    """GET /api/v1/farms/{id}/advisories returns paginated history."""
    farm_payload = {
        "farmer_name": "History Farmer",
        "county": "Kericho",
        "crop_type": "vegetables",
        "latitude": -0.2,
        "longitude": 35.0,
    }
    farm_resp = await client.post("/api/v1/farms", json=farm_payload)
    farm_id = farm_resp.json()["id"]

    mock_weather = {
        "daily": [{"date": "2026-06-07", "precipitation_probability": 10.0, "temp_max": 22.0, "wind_max": 5.0}],
        "meta": {"cached": False},
    }

    with patch("app.routers.advisories.WeatherClient") as MockWeatherClient:
        instance = MockWeatherClient.return_value
        instance.get_daily = AsyncMock(return_value=mock_weather)

        # Create 3 advisories
        for _ in range(3):
            await client.get(f"/api/v1/farms/{farm_id}/advisory")

    # Paginate
    resp = await client.get(f"/api/v1/farms/{farm_id}/advisories?limit=2&offset=0")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 2
    assert body["total"] == 3