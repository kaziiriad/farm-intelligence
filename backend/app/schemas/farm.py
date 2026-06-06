"""Pydantic v2 schemas for farm CRUD."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.farm import CropType


class FarmCreate(BaseModel):
    """Request body for POST /farms."""

    farmer_name: str = Field(..., min_length=1, max_length=255)
    county: str = Field(..., min_length=1, max_length=100)
    crop_type: CropType
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    farm_size_acres: float | None = Field(default=None, ge=0)


class FarmUpdate(BaseModel):
    """Request body for PUT /farms/{id}. All fields optional."""

    farmer_name: str | None = Field(default=None, min_length=1, max_length=255)
    county: str | None = Field(default=None, min_length=1, max_length=100)
    crop_type: CropType | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    farm_size_acres: float | None = Field(default=None, ge=0)


class FarmOut(BaseModel):
    """Response body for farm endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    farmer_name: str
    county: str
    crop_type: CropType
    latitude: float
    longitude: float
    farm_size_acres: float | None
    created_at: datetime
    updated_at: datetime


class FarmList(BaseModel):
    """Paginated list response."""

    items: list[FarmOut]
    total: int
    limit: int
    offset: int