"""Pydantic v2 schemas for tree analysis endpoints."""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TreeAnalysisOut(BaseModel):
    """Response body for a single tree analysis."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_id: UUID
    image_url: str | None
    analysis_result: dict[str, Any]
    created_at: datetime


class TreeAnalysisList(BaseModel):
    """Paginated tree analysis history."""
    items: list[TreeAnalysisOut]
    total: int
    limit: int
    offset: int