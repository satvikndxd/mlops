"""Trace (agent run) and Span (execution step) models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Trace(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "traces"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), index=True
    )
    agent_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("agent_versions.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="success", index=True)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_cost: Mapped[float] = mapped_column(Numeric(14, 6), nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    agent: Mapped["Agent"] = relationship(back_populates="traces")  # noqa: F821
    spans: Mapped[list["Span"]] = relationship(
        back_populates="trace",
        cascade="all, delete-orphan",
        order_by="Span.started_at",
    )
    cost_records: Mapped[list["CostRecord"]] = relationship(  # noqa: F821
        back_populates="trace", cascade="all, delete-orphan"
    )


class Span(UUIDMixin, Base):
    __tablename__ = "spans"

    trace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("traces.id", ondelete="CASCADE"), index=True
    )
    parent_span_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("spans.id", ondelete="SET NULL"), nullable=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False, default="llm", index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="success")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # OpenTelemetry GenAI semantic-convention fields.
    gen_ai_system: Mapped[str | None] = mapped_column(String(64), nullable=True)
    gen_ai_request_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    gen_ai_operation: Mapped[str | None] = mapped_column(String(64), nullable=True)

    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cost: Mapped[float] = mapped_column(Numeric(14, 6), nullable=False, default=0)

    # Free-form attributes (prompt, completion, tool args, etc.) for replay.
    attributes: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    trace: Mapped["Trace"] = relationship(back_populates="spans")
