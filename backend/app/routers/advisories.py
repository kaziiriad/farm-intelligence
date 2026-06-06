"""Advisory endpoint — fetches weather, scores it, persists advisory."""
import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

import httpx

from app.core.cache import RedisCache
from app.core.config import get_settings
from app.core.database import get_db
from app.models.advisory import Advisory
from app.models.farm import Farm
from app.schemas.advisory import AdvisoryList, AdvisoryOut, OperationOut
from app.services.advisory_engine import generate_advisory, generate_operation_advisory, generate_recommendations
from app.services.weather_client import WeatherClient


router = APIRouter(prefix="/api/v1/farms", tags=["advisories"])


def _build_cache() -> RedisCache:
    return RedisCache()


@router.get(
    "/{farm_id}/advisory",
    response_model=AdvisoryOut,
    responses={
        404: {"description": "Farm not found"},
        502: {"description": "WeatherAI upstream failed"},
    },
)
async def get_advisory(
    farm_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> AdvisoryOut:
    """Generate (or serve cached) 7-day agro-weather advisory for a farm."""
    farm = await db.get(Farm, farm_id)
    if farm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")

    settings = get_settings()

    # Build WeatherClient with a fake cache for now (tests inject their own)
    cache = _build_cache()
    async with httpx.AsyncClient() as http_client:
        weather_client = WeatherClient(
            http_client,
            cache,
            base_url=settings.weatherai_base_url,
            api_key=settings.weatherai_api_key.get_secret_value() if settings.weatherai_api_key else None,
        )
        try:
            weather = await weather_client.get_daily(
                lat=farm.latitude,
                lon=farm.longitude,
            )
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"WeatherAI request failed: {exc.response.status_code}",
            ) from exc

    # WeatherAI returns daily forecast at root level, not under "data"
    daily_forecast_raw = weather.get("daily", [])
    is_cached = weather.get("meta", {}).get("cached", False)

    # Normalize field names to what advisory_engine expects:
    # WeatherAI: precipitation_probability -> rain_probability, temp_max -> temperature_max, wind_max -> wind_speed_max
    daily_forecast = [
        {
            "date": day.get("date", ""),
            "rain_probability": day.get("precipitation_probability", 0.0),
            "temperature_max": day.get("temp_max", 0.0),
            "wind_speed_max": day.get("wind_max", 0.0),
            "humidity": 0.0,  # not available in daily response
        }
        for day in daily_forecast_raw
    ]

    # Score each day
    daily_scores = generate_advisory(daily_forecast)

    # Build per-day recommendations
    recommendations: dict[str, dict] = {}
    for day_score in daily_scores:
        day_conditions = {
            "rain_risk": day_score["risk_band"],
            "wind_risk": "low" if day_score["wind_score"] <= 10 else "medium" if day_score["wind_score"] <= 15 else "high",
            "rain_in_3h": False,
            "rain_probability": day_score.get("rain_probability", 0.0),
            "temperature_max": day_score.get("temperature_max", 0.0),
            "overall_risk": day_score["risk_band"],
        }
        day_recs = generate_recommendations(day_conditions)
        for op, rec in day_recs.items():
            if op not in recommendations:
                recommendations[op] = rec

    # Persist advisory
    advisory = Advisory(
        farm_id=farm_id,
        weather_snapshot=weather,
        daily_scores=daily_scores,
        recommendations=recommendations,
        cached=is_cached,
    )
    db.add(advisory)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to persist advisory")
    await db.refresh(advisory)

    return AdvisoryOut.model_validate(advisory)


@router.get(
    "/{farm_id}/advisories",
    response_model=AdvisoryList,
)
async def list_advisories(
    farm_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> AdvisoryList:
    """Paginated advisory history for a farm."""
    farm = await db.get(Farm, farm_id)
    if farm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")

    total = (
        await db.execute(
            select(func.count()).select_from(Advisory).where(Advisory.farm_id == farm_id)
        )
    ).scalar_one()

    rows = (
        await db.execute(
            select(Advisory)
            .where(Advisory.farm_id == farm_id)
            .order_by(Advisory.generated_at.desc())
            .offset(offset)
            .limit(limit)
        )
    ).scalars().all()

    return AdvisoryList(
        items=[AdvisoryOut.model_validate(r) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


VALID_OPERATIONS: list[str] = ["spraying", "irrigation", "harvesting"]


class OperationQuery(BaseModel):
    operation: Literal["spraying", "irrigation", "harvesting"]


@router.get(
    "/{farm_id}/operations/{operation}",
    response_model=OperationOut,
    responses={
        404: {"description": "Farm not found"},
        422: {"description": "Invalid operation type"},
        502: {"description": "WeatherAI upstream failed"},
    },
)
async def get_operation_advisory(
    farm_id: uuid.UUID,
    operation: str,
    db: AsyncSession = Depends(get_db),
) -> OperationOut:
    """Operation-specific advisory (spraying / irrigation / harvesting)."""
    if operation not in VALID_OPERATIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid operation type '{operation}'. Must be one of: {VALID_OPERATIONS}",
        )

    farm = await db.get(Farm, farm_id)
    if farm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")

    settings = get_settings()
    cache = _build_cache()
    async with httpx.AsyncClient() as http_client:
        weather_client = WeatherClient(
            http_client,
            cache,
            base_url=settings.weatherai_base_url,
            api_key=settings.weatherai_api_key.get_secret_value() if settings.weatherai_api_key else None,
        )
        try:
            weather = await weather_client.get_daily(
                lat=farm.latitude,
                lon=farm.longitude,
            )
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"WeatherAI request failed: {exc.response.status_code}",
            ) from exc

    daily_forecast_raw = weather.get("daily", [])
    is_cached = weather.get("meta", {}).get("cached", False)

    daily_forecast = [
        {
            "date": day.get("date", ""),
            "rain_probability": day.get("precipitation_probability", 0.0),
            "temperature_max": day.get("temp_max", 0.0),
            "wind_speed_max": day.get("wind_max", 0.0),
            "humidity": 0.0,
        }
        for day in daily_forecast_raw
    ]

    daily_scores = generate_advisory(daily_forecast)

    # Enrich daily_scores with raw fields needed by generate_operation_advisory
    for i, day in enumerate(daily_forecast):
        daily_scores[i]["rain_probability"] = day["rain_probability"]
        daily_scores[i]["temperature_max"] = day["temperature_max"]
        daily_scores[i]["wind_speed_max"] = day["wind_speed_max"]

    result = generate_operation_advisory(operation, daily_scores)

    return OperationOut(
        farm_id=farm_id,
        operation=operation,
        recommended=result["recommended"],
        priority=result.get("priority"),
        best_window=result.get("best_window"),
        reasons=result["reasons"],
        cached=is_cached,
    )