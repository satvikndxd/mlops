"""Cost analytics service."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.repositories.agent_repository import AgentRepository
from app.repositories.cost_repository import CostRepository
from app.schemas.cost import CostBreakdownItem, CostSummary, DailyCost, MonthCost


class CostService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.agents = AgentRepository(db)
        self.costs = CostRepository(db)

    def _org_id(self):
        return self.agents.get_or_create_default_org().id

    def summary(self) -> CostSummary:
        org_id = self._org_id()
        today = datetime.now(timezone.utc).date()
        month_start = today.replace(day=1)
        return CostSummary(
            today=round(self.costs.total_between(org_id, today, today), 6),
            this_month=round(self.costs.total_between(org_id, month_start, today), 6),
            all_time=round(self.costs.total_between(org_id, None, None), 6),
        )

    def by_provider(self) -> list[CostBreakdownItem]:
        org_id = self._org_id()
        return [
            CostBreakdownItem(key=r["provider"], cost=round(r["cost"], 6))
            for r in self.costs.cost_by_provider(org_id)
        ]

    def by_model(self) -> list[CostBreakdownItem]:
        return self._breakdown(self.costs.cost_by_model)

    def by_agent(self) -> list[CostBreakdownItem]:
        return self._breakdown(self.costs.cost_by_agent)

    def by_user(self) -> list[CostBreakdownItem]:
        return self._breakdown(self.costs.cost_by_user)

    def _breakdown(self, fn) -> list[CostBreakdownItem]:
        org_id = self._org_id()
        return [CostBreakdownItem(key=r["key"], cost=round(r["cost"], 6)) for r in fn(org_id)]

    def daily(self) -> list[DailyCost]:
        org_id = self._org_id()
        return [DailyCost(day=d, cost=round(c, 6)) for d, c in self.costs.daily_rows(org_id)]

    def monthly(self) -> list[MonthCost]:
        org_id = self._org_id()
        buckets: dict[str, float] = {}
        for day, cost in self.costs.daily_rows(org_id):
            key = day.strftime("%Y-%m")
            buckets[key] = buckets.get(key, 0.0) + cost
        return [MonthCost(month=k, cost=round(v, 6)) for k, v in sorted(buckets.items())]
