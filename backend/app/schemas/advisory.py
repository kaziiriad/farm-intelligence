"""Pydantic v2 schemas for advisory endpoints."""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AdvisoryDayScore(BaseModel):
    """Per-day risk score."""
    date: str
    rain_score: int = Field(..., ge=0, le=40)
    heat_score: int = Field(..., ge=0, le=25)
    wind_score: int = Field(..., ge=0, le=20)
    humidity_score: int = Field(..., ge=0, le=15)
    total_score: int = Field(..., ge=0, le=100)
    risk_band: str = Field(..., pattern="^(low|medium|high)$")


class AdvisoryOut(BaseModel):
    """Response body for advisory endpoints."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_id: UUID
    generated_at: datetime
    daily_scores: list[dict[str, Any]]
    recommendations: dict[str, Any]
    cached: bool


class AdvisoryList(BaseModel):
    """Paginated advisory history."""
    items: list[AdvisoryOut]
    total: int
    limit: int
    offset: int


class OperationOut(BaseModel):
    """Response body for operation-specific advisory."""
    farm_id: UUID
    operation: str
    recommended: bool
    priority: str | None = None  # "low", "medium", "high" for irrigation
    best_window: str | None = None  # ISO date for spraying best window
    reasons: list[str] = Field(default_factory=list)
    cached: bool