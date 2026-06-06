"""Pydantic v2 schemas for usage endpoint."""
from pydantic import BaseModel


class UsageOut(BaseModel):
    """Response body for usage endpoint."""
    total_farms: int
    total_advisories: int
    total_tree_analyses: int
    quota_limit_per_farm: int