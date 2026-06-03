"""Pydantic schemas for cost analytics."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class CostSummary(BaseModel):
    today: float
    this_month: float
    all_time: float
    currency: str = "USD"


class CostBreakdownItem(BaseModel):
    key: str
    cost: float


class MonthCost(BaseModel):
    month: str  # YYYY-MM
    cost: float


class DailyCost(BaseModel):
    day: date
    cost: float
