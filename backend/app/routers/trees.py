"""Tree analysis and quota endpoint."""
import asyncio
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import RedisCache
from app.core.config import get_settings
from app.core.database import get_db
from app.models.farm import Farm
from app.models.tree_analysis import TreeAnalysis
from app.schemas.tree import (
    TreeAnalysisList,
    TreeAnalysisOut,
)
from app.services.quota_guard import QuotaGuard
from app.services.tree_client import TreeAnalysisClient
from app.services.weather_client import WeatherClient


router = APIRouter(prefix="/api/v1/farms", tags=["trees"])


def _build_cache() -> RedisCache:
    return RedisCache()


@router.post(
    "/{farm_id}/tree-analysis",
    responses={
        404: {"description": "Farm not found"},
        429: {"description": "Quota exceeded"},
        502: {"description": "AI analysis service failed"},
        413: {"description": "Image exceeds size limit"},
    },
)
async def analyze_tree(
    farm_id: uuid.UUID,
    image: UploadFile,
    with_weather: bool = Query(False, description="Also fetch current weather for the farm"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Upload tree image, get AI health analysis via WeatherAI. Free tier: 5/month.

    When with_weather=true, fetches weather in parallel with tree analysis.
    Weather failure is non-fatal — tree result is returned with weather=null."""
    farm = await db.get(Farm, farm_id)
    if farm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")

    settings = get_settings()

    # Read and validate image before any upstream calls
    image_data = await image.read()
    max_bytes = settings.tree_image_max_mb * 1024 * 1024
    if len(image_data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds {settings.tree_image_max_mb}MB limit",
        )

    mime_type = image.content_type or "image/jpeg"

    cache = _build_cache()
    async with httpx.AsyncClient() as http_client:
        # Check quota first — WeatherAI /v1/trees/quota
        quota_guard = QuotaGuard(
            http_client,
            cache,
            base_url=settings.weatherai_base_url,
            api_key=settings.weatherai_api_key.get_secret_value() if settings.weatherai_api_key else "",
        )
        within_limit, remaining = await quota_guard.check()
        if not within_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Monthly quota exceeded. Remaining: 0",
            )

        # Build clients — both share the same http_client
        tree_client = TreeAnalysisClient(
            http_client,
            cache,
            base_url=settings.weatherai_base_url,
            api_key=settings.weatherai_api_key.get_secret_value() if settings.weatherai_api_key else "",
        )
        weather_client = WeatherClient(
            http_client,
            cache,
            base_url=settings.weatherai_base_url,
            api_key=settings.weatherai_api_key.get_secret_value() if settings.weatherai_api_key else "",
        )
        weather_client.set_db(db)

        if with_weather:
            # Fan out tree analysis + weather in parallel
            # return_exceptions=True so weather failure doesn't abort tree result
            tree_result, weather_result = await asyncio.gather(
                tree_client.analyze_tree_image(image_data, mime_type),
                weather_client.get_current(lat=farm.latitude, lon=farm.longitude),
                return_exceptions=True,
            )
            # Tree failure is fatal — raise 502
            if isinstance(tree_result, Exception):
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Tree analysis failed: {tree_result}",
                ) from tree_result
            analysis_result = tree_result
            # Weather failure is non-fatal
            if isinstance(weather_result, Exception):
                weather_data = None
            else:
                weather_data = weather_result
        else:
            try:
                analysis_result = await tree_client.analyze_tree_image(image_data, mime_type)
            except Exception as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Tree analysis failed: {exc}",
                ) from exc
            weather_data = None

    # Persist result locally
    tree_analysis = TreeAnalysis(
        farm_id=farm_id,
        image_url=None,
        analysis_result=analysis_result,
    )
    db.add(tree_analysis)
    await db.flush()
    await db.refresh(tree_analysis)

    response = {
        "id": str(tree_analysis.id),
        "farm_id": farm_id,
        "analysis_result": analysis_result,
        "quota_remaining": remaining,
    }
    if with_weather:
        response["weather"] = weather_data
    return response


@router.get("/{farm_id}/quota")
async def get_quota(
    farm_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return current tree analysis quota from WeatherAI."""
    farm = await db.get(Farm, farm_id)
    if farm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")

    settings = get_settings()
    cache = _build_cache()

    async with httpx.AsyncClient() as http_client:
        quota_guard = QuotaGuard(
            http_client,
            cache,
            base_url=settings.weatherai_base_url,
            api_key=settings.weatherai_api_key.get_secret_value() if settings.weatherai_api_key else "",
        )
        quota = await quota_guard.get_quota()

    return {
        "limit": quota.get("limit", 5),
        "used": quota.get("used", 0),
        "remaining": quota.get("remaining", 5),
    }


@router.get(
    "/{farm_id}/tree-analyses",
    response_model=TreeAnalysisList,
)
async def list_tree_analyses(
    farm_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> TreeAnalysisList:
    """Paginated tree analysis history for a farm."""
    farm = await db.get(Farm, farm_id)
    if farm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")

    total = (
        await db.execute(
            select(func.count()).select_from(TreeAnalysis).where(TreeAnalysis.farm_id == farm_id)
        )
    ).scalar_one()

    rows = (
        await db.execute(
            select(TreeAnalysis)
            .where(TreeAnalysis.farm_id == farm_id)
            .order_by(TreeAnalysis.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
    ).scalars().all()

    return TreeAnalysisList(
        items=[TreeAnalysisOut.model_validate(r) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )