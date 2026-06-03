"""AlertRule and AlertEvent models — the alerting half of the observability loop."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

# Metrics an alert rule can watch (must match MonitoringService overview fields).
ALERT_METRICS = (
    "failure_rate",
    "success_rate",
    "avg_latency_ms",
    "p95_latency_ms",
    "tool_success_rate",
    "throughput_per_hour",
    "total_cost",
)
COMPARATORS = ("gt", "gte", "lt", "lte")
SEVERITIES = ("info", "warning", "critical")


class AlertRule(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "alert_rules"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    metric: Mapped[str] = mapped_column(String(64), nullable=False)
    comparator: Mapped[str] = mapped_column(String(8), nullable=False, default="gt")
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    window_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="warning")
    channel: Mapped[str] = mapped_column(String(32), nullable=False, default="in_app")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    cooldown_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    last_triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    events: Mapped[list["AlertEvent"]] = relationship(
        back_populates="rule", cascade="all, delete-orphan"
    )


class AlertEvent(UUIDMixin, Base):
    __tablename__ = "alert_events"

    rule_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("alert_rules.id", ondelete="CASCADE"), index=True
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    metric: Mapped[str] = mapped_column(String(64), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="warning")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="firing")
    message: Mapped[str] = mapped_column(Text, nullable=False)

    rule: Mapped["AlertRule"] = relationship(back_populates="events")
