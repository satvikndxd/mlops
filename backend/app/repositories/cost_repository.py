"""Data access for cost records and cost aggregations."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select

from app.models import CostRecord
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
