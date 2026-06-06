"""Pydantic v2 schemas for usage endpoint."""
from pydantic import BaseModel


class QuotaFamily(BaseModel):
    """One quota family with used/limit/remaining."""
    used: int
    limit: int
    remaining: int


class TreesQuotaFamily(BaseModel):
    """Trees quota family from upstream /v1/trees/quota."""
    remaining: int
    limit: int
    used: int


class WeatherAiUsageOut(BaseModel):
    """Response body for WeatherAI usage endpoint — three quota families + status band."""
    api: QuotaFamily
    ai: QuotaFamily
    trees: TreesQuotaFamily
    quota_status: str  # "healthy" | "low" | "critical"


# Keep old schema for backwards compat during transition
class UsageOut(BaseModel):
    """Response body for legacy usage endpoint."""
    total_farms: int
    total_advisories: int
    total_tree_analyses: int
    quota_limit_per_farm: int