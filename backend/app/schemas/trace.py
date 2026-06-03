"""Pydantic schemas for trace ingestion and reads."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SpanIn(BaseModel):
    """A single execution step submitted by the SDK."""

    name: str
    kind: str = "llm"
    status: str = "success"
    error: str | None = None

    provider: str | None = Field(default=None, description="gen_ai.system")
    model: str | None = Field(default=None, description="gen_ai.request.model")
    operation: str | None = Field(default=None, description="gen_ai.operation.name")

    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0

    attributes: dict | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None

    # Index into the spans list identifying this span's parent (execution graph).
    parent_index: int | None = None


class TraceIn(BaseModel):
    """A complete agent run submitted by the SDK."""

    name: str
    agent_name: str
    framework: str | None = None
    agent_version: int | None = None
    model: str | None = None
    status: str = "success"
    error: str | None = None
    user_email: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    spans: list[SpanIn] = Field(default_factory=list)


class SpanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    parent_span_id: uuid.UUID | None
    name: str
    kind: str
    status: str
    error: str | None
    gen_ai_system: str | None
    gen_ai_request_model: str | None
    gen_ai_operation: str | None
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cost: float
    attributes: dict | None
    started_at: datetime | None
    ended_at: datetime | None


class TraceSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    agent_id: uuid.UUID
    status: str
    latency_ms: float
    total_tokens: int
    total_cost: float
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime


class TraceDetail(TraceSummary):
    error: str | None = None
    spans: list[SpanOut] = Field(default_factory=list)


class TraceIngestResult(BaseModel):
    trace_id: uuid.UUID
    total_cost: float
    total_tokens: int
    span_count: int
