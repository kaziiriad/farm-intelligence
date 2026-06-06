"""Quota guard — proxies tree analysis quota to WeatherAI /v1/trees/quota."""
import json
import uuid

from app.core.cache import RedisCache


class QuotaExceeded(Exception):
    """Raised when tree analysis quota is exhausted."""


class QuotaGuard:
    """Check tree analysis quota via WeatherAI upstream. No local DB write."""

    def __init__(
        self,
        http_client,
        cache: RedisCache,
        base_url: str,
        api_key: str,
    ) -> None:
        self._http = http_client
        self._cache = cache
        self._base_url = base_url
        self._api_key = api_key

    def _auth_headers(self) -> dict[str, str]:
        if self._api_key:
            return {"Authorization": f"Bearer {self._api_key}"}
        return {}

    async def get_quota(self) -> dict[str, int]:
        """Return current quota from upstream. Cached 60s to avoid burning quota on repeat calls."""
        cache_key = "weather:trees_quota"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return json.loads(cached)

        resp = await self._http.get(
            f"{self._base_url}/v1/trees/quota",
            headers=self._auth_headers(),
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
        # Cache for 60 seconds
        await self._cache.set(cache_key, json.dumps(data), ttl_s=60)
        return data

    async def check(self) -> tuple[bool, int]:
        """Return (True, remaining) if within quota. (False, 0) if exhausted."""
        quota = await self.get_quota()
        remaining = quota.get("remaining", 0)
        return (remaining > 0, remaining)