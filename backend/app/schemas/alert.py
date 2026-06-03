"""Pydantic schemas for alert rules and events."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.alert import ALERT_METRICS, COMPARATORS, SEVERITIES


class AlertRuleCreate(BaseModel):
    name: str
    metric: str = Field(description=f"One of {ALERT_METRICS}")
    comparator: str = Field(default="gt", description=f"One of {COMPARATORS}")
    threshold: float
    window_hours: int = Field(default=24, ge=1, le=24 * 90)
    severity: str = Field(default="warning", description=f"One of {SEVERITIES}")
    channel: str = "in_app"
    cooldown_minutes: int = Field(default=60, ge=0, le=24 * 60)
    enabled: bool = True


class AlertRuleUpdate(BaseModel):
    name: str | None = None
    threshold: float | None = None
    comparator: str | None = None
    window_hours: int | None = Field(default=None, ge=1, le=24 * 90)
    severity: str | None = None
    channel: str | None = None
    cooldown_minutes: int | None = Field(default=None, ge=0, le=24 * 60)
    enabled: bool | None = None


class AlertRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    metric: str
    comparator: str
    threshold: float
    window_hours: int
    severity: str
    channel: str
    enabled: bool
    cooldown_minutes: int
    last_triggered_at: datetime | None


class AlertEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rule_id: uuid.UUID
    triggered_at: datetime
    metric: str
    metric_value: float
    threshold: float
    severity: str
    status: str
    message: str


class EvaluateResult(BaseModel):
    evaluated_rules: int
    fired: list[AlertEventOut]
