"""Tree analysis and quota endpoint."""
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import RedisCache
from app.core.config import get_settings
from app.core.database import get_db
from app.models.farm import Farm
from app.models.tree_analysis import TreeAnalysis
from app.services.quota_guard import QuotaGuard
from app.services.tree_client import TreeAnalysisClient


router = APIRouter(prefix="/api/v1/farms", tags=["trees"])


def _build_cache() -> RedisCache:
    return RedisCache()


@router.post(
    "/{farm_id}/tree-analysis",
    responses={
        404: {"description": "Farm not found"},
        429: {"description": "Quota exceeded"},
        502: {"description": "AI analysis service failed"},
    },
)
async def analyze_tree(
    farm_id: uuid.UUID,
    image: UploadFile,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Upload tree image, get AI health analysis. Free tier: 100/month."""
    farm = await db.get(Farm, farm_id)
    if farm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")

    settings = get_settings()

    # Check and increment quota
    quota_guard = QuotaGuard(db)
    within_limit = await quota_guard.check_and_increment(farm_id)
    remaining = await quota_guard.get_remaining(farm_id)

    if not within_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Monthly quota exceeded. Upgrade to continue.",
        )

    # Read image data
    image_data = await image.read()
    max_bytes = settings.tree_image_max_mb * 1024 * 1024
    if len(image_data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds {settings.tree_image_max_mb}MB limit",
        )

    mime_type = image.content_type or "image/jpeg"

    # Analyze via AI
    cache = _build_cache()
    async with httpx.AsyncClient() as http_client:
        client = TreeAnalysisClient(
            http_client,
            cache,
            base_url=settings.openai_base_url,
            api_key=settings.openai_api_key.get_secret_value() if settings.openai_api_key else "",
        )
        try:
            analysis_result = await client.analyze_tree_image(image_data, mime_type)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Tree analysis failed: {exc}",
            ) from exc

    # Persist result
    tree_analysis = TreeAnalysis(
        farm_id=farm_id,
        image_url=None,  # TODO: upload to cloud storage, store URL
        analysis_result=analysis_result,
    )
    db.add(tree_analysis)
    await db.flush()
    await db.refresh(tree_analysis)

    return {
        "id": str(tree_analysis.id),
        "farm_id": farm_id,
        "analysis_result": analysis_result,
        "quota_remaining": remaining,
    }


@router.get("/{farm_id}/quota")
async def get_quota(
    farm_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return current quota usage for a farm."""
    farm = await db.get(Farm, farm_id)
    if farm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")

    settings = get_settings()
    quota_guard = QuotaGuard(db)
    remaining = await quota_guard.get_remaining(farm_id)

    return {
        "limit": settings.tree_quota_limit,
        "used": settings.tree_quota_limit - remaining,
        "remaining": remaining,
    }