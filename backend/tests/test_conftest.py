"""Verify the mock_weatherai fixture intercepts requests before they hit upstream."""
import httpx
import pytest

from tests.conftest import MockTransportBuilder


async def test_mock_transport_intercepts_request():
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json={"intercepted": True})

    transport = MockTransportBuilder(handler).build()
    async with httpx.AsyncClient(transport=transport) as client:
        resp = await client.get("https://api.weather-ai.co/v1/daily?lat=0&lon=0")

    assert resp.status_code == 200
    assert resp.json() == {"intercepted": True}
    assert len(calls) == 1
    assert "api.weather-ai.co" in str(calls[0].url)