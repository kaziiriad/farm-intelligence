"""WeatherAI client with caching, retry, and auth header secrecy."""
import json
import logging
import time
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

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
        self._db: AsyncSession | None = None

    def set_db(self, db: AsyncSession) -> None:
        """Set AsyncSession for logging WeatherAI calls to weather_api_logs."""
        self._db = db

    async def _log(
        self,
        endpoint: str,
        request_params: dict,
        status_code: int,
        response_time_ms: int,
        cache_hit: bool,
        error_message: str | None = None,
    ) -> None:
        """Persist a WeatherAI call log to weather_api_logs."""
        if self._db is None:
            return
        from app.models.weather_api_log import WeatherApiLog

        log_entry = WeatherApiLog(
            endpoint=endpoint,
            request_params=request_params,
            status_code=status_code,
            response_time_ms=response_time_ms,
            cache_hit=cache_hit,
            error_message=error_message,
        )
        self._db.add(log_entry)

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
            data = json.loads(cached)
            data["meta"]["cached"] = True
            await self._log("/v1/daily", {"lat": lat, "lon": lon}, 200, 0, True)
            return data

        params = {"lat": lat, "lon": lon, "units": units, "ai": ai}
        headers = self._auth_headers()
        t0 = time.monotonic()

        resp = await self._client.get(
            f"{self._base_url}/v1/daily",
            params=params,
            headers=headers,
            timeout=10.0,
        )

        if resp.status_code == 503:
            resp = await self._client.get(
                f"{self._base_url}/v1/daily",
                params=params,
                headers=headers,
                timeout=10.0,
            )

        elapsed_ms = int((time.monotonic() - t0) * 1000)
        status = resp.status_code
        resp.raise_for_status()

        data = resp.json()
        data["meta"] = {"cached": False}
        await self._cache.set(key, json.dumps(data), ttl_s=3600)
        await self._log("/v1/daily", params, status, elapsed_ms, False)
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
            data = json.loads(cached)
            data["meta"]["cached"] = True
            await self._log("/v1/current", {"lat": lat, "lon": lon}, 200, 0, True)
            return data

        params = {"lat": lat, "lon": lon, "units": units, "ai": ai}
        headers = self._auth_headers()
        t0 = time.monotonic()

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

        elapsed_ms = int((time.monotonic() - t0) * 1000)
        status = resp.status_code
        resp.raise_for_status()

        data = resp.json()
        data["meta"] = {"cached": False}
        await self._cache.set(key, json.dumps(data), ttl_s=300)
        await self._log("/v1/current", params, status, elapsed_ms, False)
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
            data = json.loads(cached)
            data["meta"]["cached"] = True
            await self._log("/v1/hourly", {"lat": lat, "lon": lon}, 200, 0, True)
            return data

        params = {"lat": lat, "lon": lon, "units": units, "ai": ai}
        headers = self._auth_headers()
        t0 = time.monotonic()

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

        elapsed_ms = int((time.monotonic() - t0) * 1000)
        status = resp.status_code
        resp.raise_for_status()

        data = resp.json()
        data["meta"] = {"cached": False}
        await self._cache.set(key, json.dumps(data), ttl_s=900)
        await self._log("/v1/hourly", params, status, elapsed_ms, False)
        return data

    async def get_usage(self) -> dict[str, Any]:
        """Fetch usage/quotas from WeatherAI."""
        headers = self._auth_headers()
        t0 = time.monotonic()

        resp = await self._client.get(
            f"{self._base_url}/v1/usage",
            headers=headers,
            timeout=10.0,
        )

        elapsed_ms = int((time.monotonic() - t0) * 1000)
        status = resp.status_code
        resp.raise_for_status()

        data = resp.json()
        await self._log("/v1/usage", {}, status, elapsed_ms, False)
        return data

    async def get_trees_quota(self) -> dict[str, Any]:
        """Fetch tree analysis quota from WeatherAI. Returns {remaining, limit, used}."""
        headers = self._auth_headers()
        t0 = time.monotonic()

        resp = await self._client.get(
            f"{self._base_url}/v1/trees/quota",
            headers=headers,
            timeout=10.0,
        )

        elapsed_ms = int((time.monotonic() - t0) * 1000)
        status = resp.status_code
        resp.raise_for_status()

        data = resp.json()
        await self._log("/v1/trees/quota", {}, status, elapsed_ms, False)
        return data

    def _auth_headers(self) -> dict[str, str]:
        """Return Authorization header. Key never logged."""
        if self._api_key:
            return {"Authorization": f"Bearer {self._api_key}"}
        return {}