"""Pydantic schemas for dashboard summary data."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from app.schemas.trace import TraceSummary


class DayCost(BaseModel):
    day: date
    cost: float


class ProviderCost(BaseModel):
    provider: str
    cost: float


class DashboardSummary(BaseModel):
    total_traces: int
    total_cost: float
    total_tokens: int
    avg_latency_ms: float
    success_rate: float
    active_agents: int
    cost_by_day: list[DayCost]
    cost_by_provider: list[ProviderCost]
    recent_traces: list[TraceSummary]
