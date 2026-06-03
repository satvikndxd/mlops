"""Dashboard summary aggregation service."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.agent_repository import AgentRepository
from app.repositories.cost_repository import CostRepository
from app.repositories.trace_repository import TraceRepository
from app.schemas.dashboard import DashboardSummary, DayCost, ProviderCost
from app.schemas.trace import TraceSummary


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.agents = AgentRepository(db)
        self.traces = TraceRepository(db)
        self.costs = CostRepository(db)

    def summary(self, recent_limit: int = 10) -> DashboardSummary:
        org = self.agents.get_or_create_default_org()
        agg = self.traces.aggregate(org.id)
        total = agg["total_traces"]
        success_rate = (agg["successes"] / total) if total else 0.0

        recent = self.traces.list_recent(org.id, limit=recent_limit)

        return DashboardSummary(
            total_traces=total,
            total_cost=round(agg["total_cost"], 6),
            total_tokens=agg["total_tokens"],
            avg_latency_ms=round(agg["avg_latency_ms"], 2),
            success_rate=round(success_rate, 4),
            active_agents=self.agents.count_agents(org.id),
            cost_by_day=[DayCost(**r) for r in self.costs.cost_by_day(org.id)],
            cost_by_provider=[ProviderCost(**r) for r in self.costs.cost_by_provider(org.id)],
            recent_traces=[TraceSummary.model_validate(t) for t in recent],
        )
