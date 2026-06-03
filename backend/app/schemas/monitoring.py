"""Pydantic schemas for monitoring metrics."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class MonitoringOverview(BaseModel):
    window_hours: int
    total_traces: int
    throughput_per_hour: float
    success_rate: float
    failure_rate: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    total_tokens: int
    total_cost: float
    tool_success_rate: float
    # Hallucination rate becomes populated once Evaluation (Phase 3) writes
    # eval results; until then it is reported as null (not measured).
    hallucination_rate: float | None = None


class MetricPoint(BaseModel):
    bucket: datetime
    value: float


class TimeSeries(BaseModel):
    metric: str
    bucket: str
    points: list[MetricPoint]
