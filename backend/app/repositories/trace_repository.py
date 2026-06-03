"""Data access for traces and spans."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models import Span, Trace
from app.repositories.base import BaseRepository


class TraceRepository(BaseRepository):
    def add(self, trace: Trace) -> Trace:
        self.db.add(trace)
        self.db.flush()
        return trace

    def add_span(self, span: Span) -> Span:
        self.db.add(span)
        self.db.flush()
        return span

    def get(self, trace_id: uuid.UUID) -> Trace | None:
        return self.db.scalar(
            select(Trace).where(Trace.id == trace_id).options(selectinload(Trace.spans))
        )

    def list_recent(
        self, organization_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[Trace]:
        return list(
            self.db.scalars(
                select(Trace)
                .where(Trace.organization_id == organization_id)
                .order_by(Trace.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
        )

    def count(self, organization_id: uuid.UUID) -> int:
        return self.db.scalar(
            select(func.count(Trace.id)).where(Trace.organization_id == organization_id)
        ) or 0

    def aggregate(self, organization_id: uuid.UUID) -> dict:
        row = self.db.execute(
            select(
                func.count(Trace.id),
                func.coalesce(func.sum(Trace.total_tokens), 0),
                func.coalesce(func.sum(Trace.total_cost), 0),
                func.coalesce(func.avg(Trace.latency_ms), 0.0),
                func.coalesce(
                    func.sum(case_success(Trace.status)), 0
                ),
            ).where(Trace.organization_id == organization_id)
        ).one()
        total, tokens, cost, avg_latency, successes = row
        return {
            "total_traces": int(total),
            "total_tokens": int(tokens),
            "total_cost": float(cost),
            "avg_latency_ms": float(avg_latency),
            "successes": int(successes),
        }


def case_success(status_column):
    """SUM(1) for successful traces; dialect-agnostic via CASE."""
    from sqlalchemy import case

    return case((status_column == "success", 1), else_=0)
