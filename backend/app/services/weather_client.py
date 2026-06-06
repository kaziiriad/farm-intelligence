"""WeatherAI client with caching, retry, and auth header secrecy."""
import logging
from typing import Any

import httpx

from app.core.cache import RedisCache

logger = logging.getLogger(__name__)


def _cache_key(lat: float, lon: float, endpoint: str) -> str:
    """Build cache key per PRD format: weather:{endpoint}:lat=X:lon=Y."""
    return f"weather:{endpoint}:lat={lat}:lon={lon}"


class WeatherClient:
    """Async WeatherAI client with cache-aside pattern and 503 retry."""

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        cache: RedisCache,
        base_url: str = "https://api.weather-ai.co",
        api_key: str | None = None,
    ) -> None:
        self._client = http_client
        self._cache = cache
        self._base_url = base_url
        self._api_key = api_key

    async def get_daily(
        self,
        lat: float,
        lon: float,
        *,
        units: str = "metric",
        ai: str = "false",
    ) -> dict[str, Any]:
        """Fetch 7-day daily forecast, using cache on repeat calls."""
        key = _cache_key(lat, lon, "daily")
        cached = await self._cache.get(key)
        if cached is not None:
            import json
            data = json.loads(cached)
            data["meta"]["cached"] = True
            return data

        params = {"lat": lat, "lon": lon, "units": units, "ai": ai}
        headers = self._auth_headers()

        resp = await self._client.get(
            f"{self._base_url}/v1/daily",
            params=params,
            headers=headers,
            timeout=10.0,
        )

        if resp.status_code == 503:
            # Retry once
            resp = await self._client.get(
                f"{self._base_url}/v1/daily",
                params=params,
                headers=headers,
                timeout=10.0,
            )

        resp.raise_for_status()

        import json
        data = resp.json()
        data["meta"] = {"cached": False}
        await self._cache.set(key, json.dumps(data), ttl_s=3600)
        return data

    async def get_current(
        self,
        lat: float,
        lon: float,
        *,
        units: str = "metric",
        ai: str = "false",
    ) -> dict[str, Any]:
        """Fetch current conditions."""
        key = _cache_key(lat, lon, "current")
        cached = await self._cache.get(key)
        if cached is not None:
            import json
            data = json.loads(cached)
            data["meta"]["cached"] = True
            return data

        params = {"lat": lat, "lon": lon, "units": units, "ai": ai}
        headers = self._auth_headers()

        resp = await self._client.get(
            f"{self._base_url}/v1/current",
            params=params,
            headers=headers,
            timeout=10.0,
        )

        if resp.status_code == 503:
            resp = await self._client.get(
                f"{self._base_url}/v1/current",
                params=params,
                headers=headers,
                timeout=10.0,
            )

        resp.raise_for_status()

        import json
        data = resp.json()
        data["meta"] = {"cached": False}
        await self._cache.set(key, json.dumps(data), ttl_s=300)
        return data

    async def get_hourly(
        self,
        lat: float,
        lon: float,
        *,
        units: str = "metric",
        ai: str = "false",
    ) -> dict[str, Any]:
        """Fetch hourly forecast."""
        key = _cache_key(lat, lon, "hourly")
        cached = await self._cache.get(key)
        if cached is not None:
            import json
            data = json.loads(cached)
            data["meta"]["cached"] = True
            return data

        params = {"lat": lat, "lon": lon, "units": units, "ai": ai}
        headers = self._auth_headers()

        resp = await self._client.get(
            f"{self._base_url}/v1/hourly",
            params=params,
            headers=headers,
            timeout=10.0,
        )

        if resp.status_code == 503:
            resp = await self._client.get(
                f"{self._base_url}/v1/hourly",
                params=params,
                headers=headers,
                timeout=10.0,
            )

        resp.raise_for_status()

        import json
        data = resp.json()
        data["meta"] = {"cached": False}
        await self._cache.set(key, json.dumps(data), ttl_s=900)
        return data

    async def get_usage(self) -> dict[str, Any]:
        """Fetch usage/quotas from WeatherAI."""
        headers = self._auth_headers()
        resp = await self._client.get(
            f"{self._base_url}/v1/usage",
            headers=headers,
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json()

    def _auth_headers(self) -> dict[str, str]:
        """Return Authorization header. Key never logged."""
        if self._api_key:
            return {"Authorization": f"Bearer {self._api_key}"}
        return {}