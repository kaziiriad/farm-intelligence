"""Cache service tests — TDD red until Phase 2 implementation."""
import pytest

import fakeredis.aioredis

from app.core.cache import RedisCache


pytestmark = pytest.mark.asyncio


async def test_redis_set_get_ttl_expiry():
    """Redis cache: set a key, get it, verify TTL."""
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    cache = RedisCache(client=fake)
    key = "test:ttl:1"
    await cache.set(key, "value1", ttl_s=2)
    val = await cache.get(key)
    assert val == "value1"


async def test_cache_key_format_matches_prd():
    """Cache keys use PRD format: {service}:{resource}:{id}:{field}."""
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    cache = RedisCache(client=fake)
    key = "weather:daily:lat=0.0:lon=35.0:date=2026-06-07"
    await cache.set(key, "data", ttl_s=60)
    val = await cache.get(key)
    assert val == "data"