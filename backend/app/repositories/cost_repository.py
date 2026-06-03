"""Data access for cost records and cost aggregations."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import func, select

from app.models import Agent, CostRecord, Trace, User
from app.repositories.base import BaseRepository


class CostRepository(BaseRepository):
    def add(self, record: CostRecord) -> CostRecord:
        self.db.add(record)
        self.db.flush()
        return record

    def cost_by_day(self, organization_id: uuid.UUID, limit_days: int = 30) -> list[dict]:
        rows = self.db.execute(
            select(CostRecord.day, func.coalesce(func.sum(CostRecord.cost), 0))
            .where(CostRecord.organization_id == organization_id)
            .group_by(CostRecord.day)
            .order_by(CostRecord.day.desc())
            .limit(limit_days)
        ).all()
        return [{"day": day, "cost": float(cost)} for day, cost in reversed(rows)]

    def cost_by_provider(self, organization_id: uuid.UUID) -> list[dict]:
        rows = self.db.execute(
            select(CostRecord.provider, func.coalesce(func.sum(CostRecord.cost), 0))
            .where(CostRecord.organization_id == organization_id)
            .group_by(CostRecord.provider)
            .order_by(func.sum(CostRecord.cost).desc())
        ).all()
        return [{"provider": provider, "cost": float(cost)} for provider, cost in rows]

    def cost_by_model(self, organization_id: uuid.UUID) -> list[dict]:
        rows = self.db.execute(
            select(CostRecord.model, func.coalesce(func.sum(CostRecord.cost), 0))
            .where(CostRecord.organization_id == organization_id)
            .group_by(CostRecord.model)
            .order_by(func.sum(CostRecord.cost).desc())
        ).all()
        return [{"key": model, "cost": float(cost)} for model, cost in rows]

    def cost_by_agent(self, organization_id: uuid.UUID) -> list[dict]:
        rows = self.db.execute(
            select(Agent.name, func.coalesce(func.sum(CostRecord.cost), 0))
            .join(Trace, CostRecord.trace_id == Trace.id)
            .join(Agent, Trace.agent_id == Agent.id)
            .where(CostRecord.organization_id == organization_id)
            .group_by(Agent.name)
            .order_by(func.sum(CostRecord.cost).desc())
        ).all()
        return [{"key": name, "cost": float(cost)} for name, cost in rows]

    def cost_by_user(self, organization_id: uuid.UUID) -> list[dict]:
        rows = self.db.execute(
            select(User.email, func.coalesce(func.sum(CostRecord.cost), 0))
            .join(Trace, CostRecord.trace_id == Trace.id)
            .join(User, Trace.user_id == User.id)
            .where(CostRecord.organization_id == organization_id)
            .group_by(User.email)
            .order_by(func.sum(CostRecord.cost).desc())
        ).all()
        return [{"key": email, "cost": float(cost)} for email, cost in rows]

    def total_between(
        self, organization_id: uuid.UUID, start: date | None, end: date | None
    ) -> float:
        stmt = select(func.coalesce(func.sum(CostRecord.cost), 0)).where(
            CostRecord.organization_id == organization_id
        )
        if start is not None:
            stmt = stmt.where(CostRecord.day >= start)
        if end is not None:
            stmt = stmt.where(CostRecord.day <= end)
        return float(self.db.scalar(stmt) or 0)

    def daily_rows(self, organization_id: uuid.UUID) -> list[tuple[date, float]]:
        rows = self.db.execute(
            select(CostRecord.day, func.coalesce(func.sum(CostRecord.cost), 0))
            .where(CostRecord.organization_id == organization_id)
            .group_by(CostRecord.day)
            .order_by(CostRecord.day)
        ).all()
        return [(day, float(cost)) for day, cost in rows]
