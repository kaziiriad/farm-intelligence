"""WeatherClient tests — TDD red until Phase 2 implementation."""
import httpx
import pytest

import fakeredis.aioredis

from app.core.cache import RedisCache
from tests.conftest import MockTransportBuilder


pytestmark = pytest.mark.asyncio


async def test_get_daily_uses_cache():
    """Second identical call hits cache, skips upstream."""
    from app.services.weather_client import WeatherClient

    upstream_called = False

    def handler(req: httpx.Request) -> httpx.Response:
        nonlocal upstream_called
        upstream_called = True
        return httpx.Response(200, json={
            "data": {"daily": [{"date": "2026-06-07", "temp_max": 25.0}]},
            "meta": {"cached": False},
        })

    transport = MockTransportBuilder(handler).build()
    async_client = httpx.AsyncClient(transport=transport)
    cache = RedisCache(client=fakeredis.aioredis.FakeRedis(decode_responses=True))
    client = WeatherClient(async_client, cache, base_url="https://api.weather-ai.co")

    # First call
    r1 = await client.get_daily(lat=-0.7813, lon=35.3416)
    assert r1["data"]["daily"][0]["temp_max"] == 25.0

    # Second call — should be cached
    r2 = await client.get_daily(lat=-0.7813, lon=35.3416)
    assert r2["meta"]["cached"] is True
    assert upstream_called is True  # first call hit upstream


async def test_get_daily_cache_hit_skips_upstream():
    """Cache hit means upstream never called for identical request."""
    from app.services.weather_client import WeatherClient

    call_count = 0

    def handler(req: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(200, json={
            "data": {"daily": []},
            "meta": {"cached": False},
        })

    transport = MockTransportBuilder(handler).build()
    async_client = httpx.AsyncClient(transport=transport)
    cache = RedisCache(client=fakeredis.aioredis.FakeRedis(decode_responses=True))
    client = WeatherClient(async_client, cache, base_url="https://api.weather-ai.co")

    await client.get_daily(lat=0.0, lon=0.0)
    await client.get_daily(lat=0.0, lon=0.0)
    await client.get_daily(lat=0.0, lon=0.0)

    assert call_count == 1  # only first call reached upstream


async def test_retry_once_on_503():
    """Upstream 503 triggers one retry, then succeeds."""
    from app.services.weather_client import WeatherClient

    attempts = 0

    def handler(req: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(503)
        return httpx.Response(200, json={"data": {"daily": []}, "meta": {"cached": False}})

    transport = MockTransportBuilder(handler).build()
    async_client = httpx.AsyncClient(transport=transport)
    cache = RedisCache(client=fakeredis.aioredis.FakeRedis(decode_responses=True))
    client = WeatherClient(async_client, cache, base_url="https://api.weather-ai.co")

    r = await client.get_daily(lat=0.0, lon=0.0)
    assert r["data"]["daily"] == []
    assert attempts == 2


async def test_no_retry_on_401_429():
    """401 and 429 raise immediately — no retry."""
    from app.services.weather_client import WeatherClient

    def handler_401(req: httpx.Request) -> httpx.Response:
        return httpx.Response(401)

    def handler_429(req: httpx.Request) -> httpx.Response:
        return httpx.Response(429)

    for handler in [handler_401, handler_429]:
        transport = MockTransportBuilder(handler).build()
        async_client = httpx.AsyncClient(transport=transport)
        cache = RedisCache(client=fakeredis.aioredis.FakeRedis(decode_responses=True))
        client = WeatherClient(async_client, cache, base_url="https://api.weather-ai.co")

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.get_daily(lat=0.0, lon=0.0)
        assert exc_info.value.response.status_code in (401, 429)


async def test_units_metric_and_ai_default_false():
    """Request must use units=metric and ai=false by default."""
    from app.services.weather_client import WeatherClient

    received_params: dict | None = None

    def handler(req: httpx.Request) -> httpx.Response:
        nonlocal received_params
        received_params = dict(req.url.params)
        return httpx.Response(200, json={"data": {"daily": []}, "meta": {"cached": False}})

    transport = MockTransportBuilder(handler).build()
    async_client = httpx.AsyncClient(transport=transport)
    cache = RedisCache(client=fakeredis.aioredis.FakeRedis(decode_responses=True))
    client = WeatherClient(async_client, cache, base_url="https://api.weather-ai.co")

    await client.get_daily(lat=0.0, lon=0.0)
    assert received_params is not None
    assert received_params.get("units") == "metric"
    assert received_params.get("ai") == "false"


async def test_auth_header_never_logged(caplog):
    """Auth header must not appear in any log output."""
    import logging
    from app.services.weather_client import WeatherClient

    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": {"daily": []}, "meta": {"cached": False}})

    transport = MockTransportBuilder(handler).build()
    async_client = httpx.AsyncClient(transport=transport)
    cache = RedisCache(client=fakeredis.aioredis.FakeRedis(decode_responses=True))
    client = WeatherClient(async_client, cache, base_url="https://api.weather-ai.co", api_key="sekrit")

    with caplog.at_level(logging.DEBUG):
        await client.get_daily(lat=0.0, lon=0.0)

    for record in caplog.records:
        assert "Bearer " not in record.message
        assert "sekrit" not in record.message


async def test_get_current_returns_data():
    """get_current returns current weather data."""
    from app.services.weather_client import WeatherClient

    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "data": {"current": {"temp": 22.0, "humidity": 75}},
            "meta": {"cached": False},
        })

    transport = MockTransportBuilder(handler).build()
    async_client = httpx.AsyncClient(transport=transport)
    cache = RedisCache(client=fakeredis.aioredis.FakeRedis(decode_responses=True))
    client = WeatherClient(async_client, cache, base_url="https://api.weather-ai.co")

    r = await client.get_current(lat=-0.7, lon=35.0)
    assert r["data"]["current"]["temp"] == 22.0
    assert r["meta"]["cached"] is False


async def test_get_hourly_returns_data():
    """get_hourly returns hourly forecast."""
    from app.services.weather_client import WeatherClient

    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "data": {"hourly": [{"time": "2026-06-07T10:00", "temp": 20.0}]},
            "meta": {"cached": False},
        })

    transport = MockTransportBuilder(handler).build()
    async_client = httpx.AsyncClient(transport=transport)
    cache = RedisCache(client=fakeredis.aioredis.FakeRedis(decode_responses=True))
    client = WeatherClient(async_client, cache, base_url="https://api.weather-ai.co")

    r = await client.get_hourly(lat=-0.7, lon=35.0)
    assert r["data"]["hourly"][0]["temp"] == 20.0
    assert r["meta"]["cached"] is False


async def test_get_usage_returns_quota():
    """get_usage returns quota/usage info from upstream."""
    from app.services.weather_client import WeatherClient

    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "data": {
                "api_requests": {"used": 50, "limit": 1000},
                "ai_requests": {"used": 5, "limit": 200},
                "tree_analyses": {"used": 1, "limit": 5},
            }
        })

    transport = MockTransportBuilder(handler).build()
    async_client = httpx.AsyncClient(transport=transport)
    cache = RedisCache(client=fakeredis.aioredis.FakeRedis(decode_responses=True))
    client = WeatherClient(async_client, cache, base_url="https://api.weather-ai.co", api_key="testkey")

    r = await client.get_usage()
    assert r["data"]["api_requests"]["used"] == 50
    assert r["data"]["tree_analyses"]["limit"] == 5


async def test_get_current_retries_on_503():
    """get_current retries once on 503."""
    from app.services.weather_client import WeatherClient

    attempts = 0

    def handler(req: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(503)
        return httpx.Response(200, json={"data": {"current": {}}, "meta": {"cached": False}})

    transport = MockTransportBuilder(handler).build()
    async_client = httpx.AsyncClient(transport=transport)
    cache = RedisCache(client=fakeredis.aioredis.FakeRedis(decode_responses=True))
    client = WeatherClient(async_client, cache, base_url="https://api.weather-ai.co")

    r = await client.get_current(lat=0.0, lon=0.0)
    assert r["data"]["current"] == {}
    assert attempts == 2


async def test_get_hourly_retries_on_503():
    """get_hourly retries once on 503."""
    from app.services.weather_client import WeatherClient

    attempts = 0

    def handler(req: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(503)
        return httpx.Response(200, json={"data": {"hourly": []}, "meta": {"cached": False}})

    transport = MockTransportBuilder(handler).build()
    async_client = httpx.AsyncClient(transport=transport)
    cache = RedisCache(client=fakeredis.aioredis.FakeRedis(decode_responses=True))
    client = WeatherClient(async_client, cache, base_url="https://api.weather-ai.co")

    r = await client.get_hourly(lat=0.0, lon=0.0)
    assert r["data"]["hourly"] == []
    assert attempts == 2


async def test_get_current_cache_hit():
    """Second get_current call is served from cache (lines 88-91)."""
    from app.services.weather_client import WeatherClient

    call_count = 0

    def handler(req: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(200, json={
            "data": {"current": {"temp": 22.0}},
            "meta": {"cached": False},
        })

    transport = MockTransportBuilder(handler).build()
    async_client = httpx.AsyncClient(transport=transport)
    cache = RedisCache(client=fakeredis.aioredis.FakeRedis(decode_responses=True))
    client = WeatherClient(async_client, cache, base_url="https://api.weather-ai.co")

    await client.get_current(lat=0.0, lon=0.0)
    r2 = await client.get_current(lat=0.0, lon=0.0)
    assert r2["meta"]["cached"] is True
    assert call_count == 1


async def test_get_hourly_cache_hit():
    """Second get_hourly call is served from cache (lines 131-134)."""
    from app.services.weather_client import WeatherClient

    call_count = 0

    def handler(req: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(200, json={
            "data": {"hourly": [{"time": "10:00", "temp": 18.0}]},
            "meta": {"cached": False},
        })

    transport = MockTransportBuilder(handler).build()
    async_client = httpx.AsyncClient(transport=transport)
    cache = RedisCache(client=fakeredis.aioredis.FakeRedis(decode_responses=True))
    client = WeatherClient(async_client, cache, base_url="https://api.weather-ai.co")

    await client.get_hourly(lat=0.0, lon=0.0)
    r2 = await client.get_hourly(lat=0.0, lon=0.0)
    assert r2["meta"]["cached"] is True
    assert call_count == 1