"""Farm CRUD endpoint tests. TDD red — these should fail until Phase 1 is implemented."""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


pytestmark = pytest.mark.asyncio


VALID_FARM = {
    "farmer_name": "John Mwangi",
    "county": "Bomet",
    "crop_type": "tea",
    "latitude": -0.7813,
    "longitude": 35.3416,
    "farm_size_acres": 2.5,
}


async def test_create_farm_returns_201_with_id(client: AsyncClient):
    response = await client.post("/api/v1/farms", json=VALID_FARM)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["farmer_name"] == "John Mwangi"
    assert body["crop_type"] == "tea"
    assert "id" in body
    assert "created_at" in body


async def test_create_farm_validates_lat_lon(client: AsyncClient):
    bad_lat = {**VALID_FARM, "latitude": 91.0}
    bad_lon = {**VALID_FARM, "longitude": 181.0}
    assert (await client.post("/api/v1/farms", json=bad_lat)).status_code == 422
    assert (await client.post("/api/v1/farms", json=bad_lon)).status_code == 422


async def test_create_farm_rejects_unsupported_crop(client: AsyncClient):
    bad_crop = {**VALID_FARM, "crop_type": "banana"}
    response = await client.post("/api/v1/farms", json=bad_crop)
    assert response.status_code == 422


async def test_create_farm_rejects_duplicate_farmer_coords(client: AsyncClient):
    r1 = await client.post("/api/v1/farms", json=VALID_FARM)
    assert r1.status_code == 201
    r2 = await client.post("/api/v1/farms", json=VALID_FARM)
    assert r2.status_code == 409


async def test_create_farm_requires_all_mandatory_fields(client: AsyncClient):
    for key in ("farmer_name", "county", "crop_type", "latitude", "longitude"):
        payload = {k: v for k, v in VALID_FARM.items() if k != key}
        response = await client.post("/api/v1/farms", json=payload)
        assert response.status_code == 422, f"missing {key} should be 422"


async def test_list_farms_pagination(client: AsyncClient):
    for i in range(3):
        payload = {**VALID_FARM, "farmer_name": f"Farmer {i}"}
        await client.post("/api/v1/farms", json=payload)
    response = await client.get("/api/v1/farms?limit=2&offset=0")
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["total"] == 3


async def test_get_update_delete_farm(client: AsyncClient):
    # Create
    r = await client.post("/api/v1/farms", json=VALID_FARM)
    farm_id = r.json()["id"]

    # Get
    r = await client.get(f"/api/v1/farms/{farm_id}")
    assert r.status_code == 200
    assert r.json()["farmer_name"] == "John Mwangi"

    # Update
    r = await client.put(f"/api/v1/farms/{farm_id}", json={"county": "Kericho"})
    assert r.status_code == 200
    assert r.json()["county"] == "Kericho"

    # Delete
    r = await client.delete(f"/api/v1/farms/{farm_id}")
    assert r.status_code == 204

    # Get after delete → 404
    r = await client.get(f"/api/v1/farms/{farm_id}")
    assert r.status_code == 404


async def test_get_unknown_farm_returns_404(client: AsyncClient):
    response = await client.get("/api/v1/farms/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404