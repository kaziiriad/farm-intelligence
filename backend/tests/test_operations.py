"""Operation-specific advisory endpoint tests."""
from unittest.mock import AsyncMock, patch
import uuid

import pytest

from app.models.advisory import Advisory


pytestmark = pytest.mark.asyncio


async def test_spraying_not_recommended_rain_high(client):
    """Spraying blocked when rain risk is high."""
    farm_payload = {
        "farmer_name": "Spray Rain Farmer",
        "county": "Nairobi",
        "crop_type": "tea",
        "latitude": -1.0,
        "longitude": 37.0,
    }
    farm_resp = await client.post("/api/v1/farms", json=farm_payload)
    farm_id = farm_resp.json()["id"]

    mock_weather = {
        "daily": [
            {"date": "2026-06-07", "precipitation_probability": 80.0, "temp_max": 25.0, "wind_max": 8.0},
        ],
        "meta": {"cached": False},
    }

    with patch("app.routers.advisories.WeatherClient") as MockWeatherClient:
        instance = MockWeatherClient.return_value
        instance.get_daily = AsyncMock(return_value=mock_weather)

        resp = await client.get(f"/api/v1/farms/{farm_id}/operations/spraying")

    assert resp.status_code == 200
    body = resp.json()
    assert body["operation"] == "spraying"
    assert body["recommended"] is False
    assert any("rain" in r.lower() for r in body["reasons"])


async def test_spraying_not_recommended_wind_high(client):
    """Spraying blocked when wind risk is high."""
    farm_payload = {
        "farmer_name": "Spray Wind Farmer",
        "county": "Nairobi",
        "crop_type": "tea",
        "latitude": -1.0,
        "longitude": 37.0,
    }
    farm_resp = await client.post("/api/v1/farms", json=farm_payload)
    farm_id = farm_resp.json()["id"]

    # wind >= 30 gives wind_score=20 (high), rain stays low (10% -> rain_score=0)
    mock_weather = {
        "daily": [
            {"date": "2026-06-07", "precipitation_probability": 10.0, "temp_max": 25.0, "wind_max": 30.0},
        ],
        "meta": {"cached": False},
    }

    with patch("app.routers.advisories.WeatherClient") as MockWeatherClient:
        instance = MockWeatherClient.return_value
        instance.get_daily = AsyncMock(return_value=mock_weather)

        resp = await client.get(f"/api/v1/farms/{farm_id}/operations/spraying")

    assert resp.status_code == 200
    body = resp.json()
    assert body["recommended"] is False
    assert any("wind" in r.lower() for r in body["reasons"])


async def test_spraying_recommended_low_risk(client):
    """Spraying allowed when rain and wind are low."""
    farm_payload = {
        "farmer_name": "Spray Safe Farmer",
        "county": "Nairobi",
        "crop_type": "tea",
        "latitude": -1.0,
        "longitude": 37.0,
    }
    farm_resp = await client.post("/api/v1/farms", json=farm_payload)
    farm_id = farm_resp.json()["id"]

    mock_weather = {
        "daily": [
            {"date": "2026-06-07", "precipitation_probability": 10.0, "temp_max": 25.0, "wind_max": 5.0},
        ],
        "meta": {"cached": False},
    }

    with patch("app.routers.advisories.WeatherClient") as MockWeatherClient:
        instance = MockWeatherClient.return_value
        instance.get_daily = AsyncMock(return_value=mock_weather)

        resp = await client.get(f"/api/v1/farms/{farm_id}/operations/spraying")

    assert resp.status_code == 200
    body = resp.json()
    assert body["operation"] == "spraying"
    assert body["recommended"] is True
    assert body["best_window"] is not None


async def test_irrigation_high_need_hot_dry(client):
    """Irrigation high priority when hot and dry."""
    farm_payload = {
        "farmer_name": "Irrig Hot Farmer",
        "county": "Nairobi",
        "crop_type": "tea",
        "latitude": -1.0,
        "longitude": 37.0,
    }
    farm_resp = await client.post("/api/v1/farms", json=farm_payload)
    farm_id = farm_resp.json()["id"]

    mock_weather = {
        "daily": [
            {"date": "2026-06-07", "precipitation_probability": 10.0, "temp_max": 35.0, "wind_max": 5.0},
        ],
        "meta": {"cached": False},
    }

    with patch("app.routers.advisories.WeatherClient") as MockWeatherClient:
        instance = MockWeatherClient.return_value
        instance.get_daily = AsyncMock(return_value=mock_weather)

        resp = await client.get(f"/api/v1/farms/{farm_id}/operations/irrigation")

    assert resp.status_code == 200
    body = resp.json()
    assert body["operation"] == "irrigation"
    assert body["priority"] == "high"


async def test_irrigation_low_need_rainy(client):
    """Irrigation low priority when rain probability is high."""
    farm_payload = {
        "farmer_name": "Irrig Rain Farmer",
        "county": "Nairobi",
        "crop_type": "tea",
        "latitude": -1.0,
        "longitude": 37.0,
    }
    farm_resp = await client.post("/api/v1/farms", json=farm_payload)
    farm_id = farm_resp.json()["id"]

    mock_weather = {
        "daily": [
            {"date": "2026-06-07", "precipitation_probability": 80.0, "temp_max": 25.0, "wind_max": 5.0},
        ],
        "meta": {"cached": False},
    }

    with patch("app.routers.advisories.WeatherClient") as MockWeatherClient:
        instance = MockWeatherClient.return_value
        instance.get_daily = AsyncMock(return_value=mock_weather)

        resp = await client.get(f"/api/v1/farms/{farm_id}/operations/irrigation")

    assert resp.status_code == 200
    body = resp.json()
    assert body["operation"] == "irrigation"
    assert body["priority"] == "low"


async def test_harvesting_blocked_high_risk(client):
    """Harvesting not recommended when overall risk is high."""
    farm_payload = {
        "farmer_name": "Harvest Risk Farmer",
        "county": "Nairobi",
        "crop_type": "tea",
        "latitude": -1.0,
        "longitude": 37.0,
    }
    farm_resp = await client.post("/api/v1/farms", json=farm_payload)
    farm_id = farm_resp.json()["id"]

    # precip=95% -> rain_score=40, temp=38 -> heat_score=25, wind=32 -> wind_score=20
    # total=85 -> high risk band
    mock_weather = {
        "daily": [
            {"date": "2026-06-07", "precipitation_probability": 95.0, "temp_max": 38.0, "wind_max": 32.0},
        ],
        "meta": {"cached": False},
    }

    with patch("app.routers.advisories.WeatherClient") as MockWeatherClient:
        instance = MockWeatherClient.return_value
        instance.get_daily = AsyncMock(return_value=mock_weather)

        resp = await client.get(f"/api/v1/farms/{farm_id}/operations/harvesting")

    assert resp.status_code == 200
    body = resp.json()
    assert body["operation"] == "harvesting"
    assert body["recommended"] is False


async def test_harvesting_safe_low_risk(client):
    """Harvesting recommended when overall risk is low."""
    farm_payload = {
        "farmer_name": "Harvest Safe Farmer",
        "county": "Nairobi",
        "crop_type": "tea",
        "latitude": -1.0,
        "longitude": 37.0,
    }
    farm_resp = await client.post("/api/v1/farms", json=farm_payload)
    farm_id = farm_resp.json()["id"]

    mock_weather = {
        "daily": [
            {"date": "2026-06-07", "precipitation_probability": 5.0, "temp_max": 22.0, "wind_max": 5.0},
        ],
        "meta": {"cached": False},
    }

    with patch("app.routers.advisories.WeatherClient") as MockWeatherClient:
        instance = MockWeatherClient.return_value
        instance.get_daily = AsyncMock(return_value=mock_weather)

        resp = await client.get(f"/api/v1/farms/{farm_id}/operations/harvesting")

    assert resp.status_code == 200
    body = resp.json()
    assert body["operation"] == "harvesting"
    assert body["recommended"] is True


async def test_operations_404_unknown_farm(client):
    """Unknown farm returns 404."""
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/farms/{fake_id}/operations/spraying")
    assert resp.status_code == 404


async def test_operations_invalid_type_422(client):
    """Invalid operation type returns 422."""
    farm_payload = {
        "farmer_name": "Invalid Type Farmer",
        "county": "Nairobi",
        "crop_type": "tea",
        "latitude": -1.0,
        "longitude": 37.0,
    }
    farm_resp = await client.post("/api/v1/farms", json=farm_payload)
    farm_id = farm_resp.json()["id"]

    resp = await client.get(f"/api/v1/farms/{farm_id}/operations/invalid_type")
    assert resp.status_code == 422


async def test_planting_blocked_heavy_rain(client):
    """Planting blocked when heavy rain expected (rain_score >= 20)."""
    farm_payload = {
        "farmer_name": "Plant Rain Farmer",
        "county": "Nairobi",
        "crop_type": "tea",
        "latitude": -1.0,
        "longitude": 37.0,
    }
    farm_resp = await client.post("/api/v1/farms", json=farm_payload)
    farm_id = farm_resp.json()["id"]

    mock_weather = {
        "daily": [
            {"date": "2026-06-07", "precipitation_probability": 45.0, "temp_max": 25.0, "wind_max": 8.0},
        ],
        "meta": {"cached": False},
    }

    with patch("app.routers.advisories.WeatherClient") as MockWeatherClient:
        instance = MockWeatherClient.return_value
        instance.get_daily = AsyncMock(return_value=mock_weather)

        resp = await client.get(f"/api/v1/farms/{farm_id}/operations/planting")

    assert resp.status_code == 200
    body = resp.json()
    assert body["operation"] == "planting"
    assert body["recommended"] is False
    assert any("washout" in r.lower() for r in body["reasons"])


async def test_planting_allowed_light_rain(client):
    """Planting allowed when rain is light."""
    farm_payload = {
        "farmer_name": "Plant Safe Farmer",
        "county": "Nairobi",
        "crop_type": "tea",
        "latitude": -1.0,
        "longitude": 37.0,
    }
    farm_resp = await client.post("/api/v1/farms", json=farm_payload)
    farm_id = farm_resp.json()["id"]

    mock_weather = {
        "daily": [
            {"date": "2026-06-07", "precipitation_probability": 15.0, "temp_max": 25.0, "wind_max": 8.0},
        ],
        "meta": {"cached": False},
    }

    with patch("app.routers.advisories.WeatherClient") as MockWeatherClient:
        instance = MockWeatherClient.return_value
        instance.get_daily = AsyncMock(return_value=mock_weather)

        resp = await client.get(f"/api/v1/farms/{farm_id}/operations/planting")

    assert resp.status_code == 200
    body = resp.json()
    assert body["operation"] == "planting"
    assert body["recommended"] is True


async def test_field_work_blocked_high_risk(client):
    """Field work blocked when overall risk is high."""
    farm_payload = {
        "farmer_name": "Field High Risk Farmer",
        "county": "Nairobi",
        "crop_type": "tea",
        "latitude": -1.0,
        "longitude": 37.0,
    }
    farm_resp = await client.post("/api/v1/farms", json=farm_payload)
    farm_id = farm_resp.json()["id"]

    mock_weather = {
        "daily": [
            {"date": "2026-06-07", "precipitation_probability": 90.0, "temp_max": 38.0, "wind_max": 35.0},
        ],
        "meta": {"cached": False},
    }

    with patch("app.routers.advisories.WeatherClient") as MockWeatherClient:
        instance = MockWeatherClient.return_value
        instance.get_daily = AsyncMock(return_value=mock_weather)

        resp = await client.get(f"/api/v1/farms/{farm_id}/operations/field_work")

    assert resp.status_code == 200
    body = resp.json()
    assert body["operation"] == "field_work"
    assert body["recommended"] is False


async def test_field_work_safe_low_risk(client):
    """Field work safe when overall risk is low."""
    farm_payload = {
        "farmer_name": "Field Safe Farmer",
        "county": "Nairobi",
        "crop_type": "tea",
        "latitude": -1.0,
        "longitude": 37.0,
    }
    farm_resp = await client.post("/api/v1/farms", json=farm_payload)
    farm_id = farm_resp.json()["id"]

    mock_weather = {
        "daily": [
            {"date": "2026-06-07", "precipitation_probability": 5.0, "temp_max": 22.0, "wind_max": 5.0},
        ],
        "meta": {"cached": False},
    }

    with patch("app.routers.advisories.WeatherClient") as MockWeatherClient:
        instance = MockWeatherClient.return_value
        instance.get_daily = AsyncMock(return_value=mock_weather)

        resp = await client.get(f"/api/v1/farms/{farm_id}/operations/field_work")

    assert resp.status_code == 200
    body = resp.json()
    assert body["operation"] == "field_work"
    assert body["recommended"] is True


async def test_operations_with_date_fetches_hourly_and_computes_window(client):
    """Operations endpoint with date param fetches hourly and computes best window.

    Uses irrigation (no daily best_window) so window_date comes from hourly computation.
    """
    farm_payload = {
        "farmer_name": "Window Farmer",
        "county": "Nairobi",
        "crop_type": "tea",
        "latitude": -1.0,
        "longitude": 37.0,
    }
    farm_resp = await client.post("/api/v1/farms", json=farm_payload)
    farm_id = farm_resp.json()["id"]

    # irrigation has no daily best_window, so window_date comes from hourly
    mock_daily = {
        "daily": [
            {"date": "2026-06-07", "precipitation_probability": 50.0, "temp_max": 25.0, "wind_max": 5.0},
        ],
        "meta": {"cached": False},
    }
    mock_hourly = {
        "hourly": [
            {"time": "06:00", "date": "2026-06-07", "rain_probability": 30, "wind_speed": 10},
            {"time": "07:00", "date": "2026-06-07", "rain_probability": 20, "wind_speed": 8},
            {"time": "08:00", "date": "2026-06-07", "rain_probability": 60, "wind_speed": 5},
        ],
        "meta": {"cached": False},
    }

    with patch("app.routers.advisories.WeatherClient") as MockWeatherClient:
        instance = MockWeatherClient.return_value
        instance.get_daily = AsyncMock(return_value=mock_daily)
        instance.get_hourly = AsyncMock(return_value=mock_hourly)

        resp = await client.get(f"/api/v1/farms/{farm_id}/operations/irrigation?date=2026-06-07")

    assert resp.status_code == 200
    body = resp.json()
    assert body["operation"] == "irrigation"
    assert body["best_window"] is not None
    assert body["window_date"] == "2026-06-07"