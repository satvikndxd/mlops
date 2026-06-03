"""Data access for monitoring metrics (time-windowed reads over traces/spans)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select

from app.models import Span, Trace
from app.repositories.base import BaseRepository


class MonitoringRepository(BaseRepository):
    def traces_in_window(self, organization_id: uuid.UUID, since: datetime) -> list[Trace]:
        return list(
            self.db.scalars(
                select(Trace)
                .where(Trace.organization_id == organization_id, Trace.created_at >= since)
                .order_by(Trace.created_at)
            )
        )

    def tool_span_counts(self, organization_id: uuid.UUID, since: datetime) -> tuple[int, int]:
        """Return (total_tool_spans, successful_tool_spans) in the window."""
        base = (
            select(func.count(Span.id))
            .join(Trace, Span.trace_id == Trace.id)
            .where(
                Trace.organization_id == organization_id,
                Span.kind == "tool",
                Trace.created_at >= since,
            )
        )
        total = self.db.scalar(base) or 0
        success = self.db.scalar(base.where(Span.status == "success")) or 0
        return int(total), int(success)
