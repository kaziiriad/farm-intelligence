"""Redis cache — async, backed by redis.asyncio."""
from __future__ import annotations

from typing import TYPE_CHECKING

import redis.asyncio as redis

if TYPE_CHECKING:
    from app.core.config import Settings


_redis_client: redis.Redis | None = None


def get_redis_client() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        from app.core.config import get_settings
        _redis_client = redis.from_url(
            get_settings().redis_url,
            decode_responses=True,
        )
    return _redis_client


async def close_redis_client() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


class RedisCache:
    """Async Redis cache with get/set and TTL.

    Accepts an optional client (for tests using fakeredis). Defaults to the
    process-global client from get_redis_client().
    """

    def __init__(self, client: redis.Redis | None = None) -> None:
        self._client = client if client is not None else get_redis_client()

    async def get(self, key: str) -> str | None:
        val = await self._client.get(key)
        if isinstance(val, bytes):
            return val.decode("utf-8")
        return val

    async def set(self, key: str, value: str, ttl_s: int) -> None:
        await self._client.set(key, value, ex=ttl_s)