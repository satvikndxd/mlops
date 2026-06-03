"""Monitoring service — overview snapshot and time-series aggregation.

Aggregation is done in Python after a windowed query so it is identical on
SQLite and PostgreSQL. This is fine at AgentForge's current scale; the same
service can later push these reads through Redis caching / Kafka rollups.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import Trace
from app.repositories.agent_repository import AgentRepository
from app.repositories.monitoring_repository import MonitoringRepository
from app.schemas.monitoring import MetricPoint, MonitoringOverview, TimeSeries

VALID_METRICS = {
    "volume",
    "latency_avg",
    "latency_p95",
    "failure_rate",
    "tokens",
    "cost",
}
BUCKETS = {"hour": timedelta(hours=1), "day": timedelta(days=1)}


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    k = (len(ordered) - 1) * pct
    lower = int(k)
    upper = min(lower + 1, len(ordered) - 1)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (k - lower)


class MonitoringService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.agents = AgentRepository(db)
        self.repo = MonitoringRepository(db)

    def _org_id(self):
        return self.agents.get_or_create_default_org().id

    def overview(self, window_hours: int = 24) -> MonitoringOverview:
        org_id = self._org_id()
        since = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        traces = self.repo.traces_in_window(org_id, since)

        total = len(traces)
        latencies = [t.latency_ms for t in traces]
        successes = sum(1 for t in traces if t.status == "success")
        tokens = sum(t.total_tokens for t in traces)
        cost = sum(float(t.total_cost) for t in traces)
        tool_total, tool_ok = self.repo.tool_span_counts(org_id, since)

        return MonitoringOverview(
            window_hours=window_hours,
            total_traces=total,
            throughput_per_hour=round(total / window_hours, 3) if window_hours else 0.0,
            success_rate=round(successes / total, 4) if total else 0.0,
            failure_rate=round((total - successes) / total, 4) if total else 0.0,
            avg_latency_ms=round(sum(latencies) / total, 2) if total else 0.0,
            p50_latency_ms=round(_percentile(latencies, 0.50), 2),
            p95_latency_ms=round(_percentile(latencies, 0.95), 2),
            total_tokens=tokens,
            total_cost=round(cost, 6),
            tool_success_rate=round(tool_ok / tool_total, 4) if tool_total else 0.0,
            hallucination_rate=None,
        )

    def timeseries(self, metric: str, hours: int = 168, bucket: str = "day") -> TimeSeries:
        if metric not in VALID_METRICS:
            raise ValueError(f"Unknown metric '{metric}'. Valid: {sorted(VALID_METRICS)}")
        if bucket not in BUCKETS:
            raise ValueError(f"Unknown bucket '{bucket}'. Valid: {sorted(BUCKETS)}")

        org_id = self._org_id()
        step = BUCKETS[bucket]
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        traces = self.repo.traces_in_window(org_id, since)

        groups: dict[datetime, list[Trace]] = {}
        for trace in traces:
            key = self._bucket_key(trace.created_at, bucket)
            groups.setdefault(key, []).append(trace)

        points = [
            MetricPoint(bucket=key, value=self._reduce(metric, group))
            for key, group in sorted(groups.items())
        ]
        return TimeSeries(metric=metric, bucket=bucket, points=points)

    @staticmethod
    def _bucket_key(value: datetime, bucket: str) -> datetime:
        value = value.astimezone(timezone.utc)
        if bucket == "hour":
            return value.replace(minute=0, second=0, microsecond=0)
        return value.replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def _reduce(metric: str, group: list[Trace]) -> float:
        n = len(group)
        if metric == "volume":
            return float(n)
        if metric == "tokens":
            return float(sum(t.total_tokens for t in group))
        if metric == "cost":
            return round(sum(float(t.total_cost) for t in group), 6)
        if metric == "latency_avg":
            return round(sum(t.latency_ms for t in group) / n, 2) if n else 0.0
        if metric == "latency_p95":
            return round(_percentile([t.latency_ms for t in group], 0.95), 2)
        if metric == "failure_rate":
            failures = sum(1 for t in group if t.status != "success")
            return round(failures / n, 4) if n else 0.0
        return 0.0
