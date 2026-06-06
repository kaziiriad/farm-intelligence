"""Usage aggregation endpoint."""
import asyncio

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas.usage import WeatherAiUsageOut
from app.services.weather_client import WeatherClient


router = APIRouter(prefix="/api/v1/weather-ai", tags=["usage"])


def _build_cache():
    from app.core.cache import RedisCache
    return RedisCache()


@router.get("/usage", response_model=WeatherAiUsageOut)
async def get_weatherai_usage(
    db: AsyncSession = Depends(get_db),
) -> WeatherAiUsageOut:
    """Three quota families (api, ai, trees) + quota_status band from WeatherAI upstream.

    quota_status: healthy (>30% remaining), low (>10%), critical (≤10%).
    """
    settings = get_settings()
    cache = _build_cache()

    async with httpx.AsyncClient() as http_client:
        weather_client = WeatherClient(
            http_client,
            cache,
            base_url=settings.weatherai_base_url,
            api_key=settings.weatherai_api_key.get_secret_value() if settings.weatherai_api_key else None,
        )
        weather_client.set_db(db)
        try:
            usage_raw, trees_raw = await asyncio.gather(
                weather_client.get_usage(),
                weather_client.get_trees_quota(),
            )
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"WeatherAI request failed: {exc.response.status_code}",
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"WeatherAI request failed: {exc}",
            ) from exc

    data = usage_raw.get("data", {})

    api_used = data.get("api_requests", {}).get("used", 0)
    api_limit = data.get("api_requests", {}).get("limit", 0)
    api_remaining = max(0, api_limit - api_used)

    ai_used = data.get("ai_requests", {}).get("used", 0)
    ai_limit = data.get("ai_requests", {}).get("limit", 0)
    ai_remaining = max(0, ai_limit - ai_used)

    trees_remaining = trees_raw.get("remaining", 0)
    trees_limit = trees_raw.get("limit", 0)
    trees_used = trees_raw.get("used", 0)

    # Determine band from trees quota (most restrictive)
    trees_ratio = 0.0 if trees_limit == 0 else trees_remaining / trees_limit
    if trees_ratio > 0.3:
        quota_status = "healthy"
    elif trees_ratio > 0.1:
        quota_status = "low"
    else:
        quota_status = "critical"

    return WeatherAiUsageOut(
        api={"used": api_used, "limit": api_limit, "remaining": api_remaining},
        ai={"used": ai_used, "limit": ai_limit, "remaining": ai_remaining},
        trees={"remaining": trees_remaining, "limit": trees_limit, "used": trees_used},
        quota_status=quota_status,
    )