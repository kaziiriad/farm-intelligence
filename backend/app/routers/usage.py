"""Usage aggregation endpoint."""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.models.advisory import Advisory
from app.models.farm import Farm
from app.models.tree_analysis import TreeAnalysis
from app.schemas.usage import UsageOut


router = APIRouter(prefix="/api/v1", tags=["usage"])


@router.get("/usage", response_model=UsageOut)
async def get_usage(
    db: AsyncSession = Depends(get_db),
) -> UsageOut:
    """Aggregated API usage summary across all farms."""
    settings = get_settings()

    total_farms = (
        await db.execute(select(func.count()).select_from(Farm))
    ).scalar_one()

    total_advisories = (
        await db.execute(select(func.count()).select_from(Advisory))
    ).scalar_one()

    total_tree_analyses = (
        await db.execute(select(func.count()).select_from(TreeAnalysis))
    ).scalar_one()

    return UsageOut(
        total_farms=total_farms,
        total_advisories=total_advisories,
        total_tree_analyses=total_tree_analyses,
        quota_limit_per_farm=settings.tree_quota_limit,
    )