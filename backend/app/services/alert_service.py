"""Alert service — rule CRUD and the evaluation engine.

Evaluation reads the same MonitoringService metrics that power the dashboards,
so an alert fires on exactly the number an operator sees. This closes the
observability loop: Trace → Metric → Alert.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.metrics import REGISTRY
from app.models import AlertEvent, AlertRule
from app.models.alert import ALERT_METRICS, COMPARATORS, SEVERITIES
from app.repositories.agent_repository import AgentRepository
from app.repositories.alert_repository import AlertRepository
from app.schemas.alert import AlertRuleCreate, AlertRuleUpdate
from app.services.monitoring_service import MonitoringService

try:
    from prometheus_client import Counter

    ALERTS_FIRED = Counter(
        "agentforge_alerts_fired_total",
        "Total alert events fired.",
        ["severity"],
        registry=REGISTRY,
    )
except ValueError:  # pragma: no cover - already registered on reload
    ALERTS_FIRED = None


def _compare(value: float, comparator: str, threshold: float) -> bool:
    return {
        "gt": value > threshold,
        "gte": value >= threshold,
        "lt": value < threshold,
        "lte": value <= threshold,
    }[comparator]


class AlertService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.agents = AgentRepository(db)
        self.repo = AlertRepository(db)
        self.monitoring = MonitoringService(db)

    def _org_id(self):
        return self.agents.get_or_create_default_org().id

    # --- Rule CRUD -----------------------------------------------------
    def create_rule(self, payload: AlertRuleCreate) -> AlertRule:
        self._validate(payload.metric, payload.comparator, payload.severity)
        rule = AlertRule(
            organization_id=self._org_id(),
            name=payload.name,
            metric=payload.metric,
            comparator=payload.comparator,
            threshold=payload.threshold,
            window_hours=payload.window_hours,
            severity=payload.severity,
            channel=payload.channel,
            cooldown_minutes=payload.cooldown_minutes,
            enabled=payload.enabled,
        )
        self.repo.add_rule(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def update_rule(self, rule_id: uuid.UUID, payload: AlertRuleUpdate) -> AlertRule | None:
        rule = self.repo.get_rule(rule_id)
        if rule is None:
            return None
        data = payload.model_dump(exclude_unset=True)
        if "metric" in data or "comparator" in data or "severity" in data:
            self._validate(
                data.get("metric", rule.metric),
                data.get("comparator", rule.comparator),
                data.get("severity", rule.severity),
            )
        for key, value in data.items():
            setattr(rule, key, value)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def delete_rule(self, rule_id: uuid.UUID) -> bool:
        rule = self.repo.get_rule(rule_id)
        if rule is None:
            return False
        self.repo.delete_rule(rule)
        self.db.commit()
        return True

    def list_rules(self) -> list[AlertRule]:
        return self.repo.list_rules(self._org_id())

    def list_events(self, limit: int = 100) -> list[AlertEvent]:
        return self.repo.list_events(self._org_id(), limit=limit)

    # --- Evaluation engine --------------------------------------------
    def evaluate(self) -> list[AlertEvent]:
        org_id = self._org_id()
        rules = self.repo.list_rules(org_id, enabled_only=True)
        now = datetime.now(timezone.utc)
        fired: list[AlertEvent] = []

        # Cache overviews per window so multiple rules share one computation.
        overview_cache: dict[int, dict] = {}

        for rule in rules:
            if self._in_cooldown(rule, now):
                continue
            if rule.window_hours not in overview_cache:
                overview_cache[rule.window_hours] = self.monitoring.overview(
                    rule.window_hours
                ).model_dump()
            metrics = overview_cache[rule.window_hours]
            value = metrics.get(rule.metric)
            if value is None:
                continue

            if _compare(float(value), rule.comparator, rule.threshold):
                event = AlertEvent(
                    rule_id=rule.id,
                    organization_id=org_id,
                    triggered_at=now,
                    metric=rule.metric,
                    metric_value=float(value),
                    threshold=rule.threshold,
                    severity=rule.severity,
                    status="firing",
                    message=(
                        f"{rule.name}: {rule.metric}={float(value):.4g} "
                        f"{rule.comparator} {rule.threshold:.4g} "
                        f"(window {rule.window_hours}h)"
                    ),
                )
                self.repo.add_event(event)
                rule.last_triggered_at = now
                fired.append(event)
                if ALERTS_FIRED is not None:
                    ALERTS_FIRED.labels(severity=rule.severity).inc()

        self.db.commit()
        for event in fired:
            self.db.refresh(event)
        return fired

    @staticmethod
    def _in_cooldown(rule: AlertRule, now: datetime) -> bool:
        if rule.last_triggered_at is None or rule.cooldown_minutes <= 0:
            return False
        last = rule.last_triggered_at
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        return now - last < timedelta(minutes=rule.cooldown_minutes)

    @staticmethod
    def _validate(metric: str, comparator: str, severity: str) -> None:
        if metric not in ALERT_METRICS:
            raise ValueError(f"Invalid metric '{metric}'. Valid: {ALERT_METRICS}")
        if comparator not in COMPARATORS:
            raise ValueError(f"Invalid comparator '{comparator}'. Valid: {COMPARATORS}")
        if severity not in SEVERITIES:
            raise ValueError(f"Invalid severity '{severity}'. Valid: {SEVERITIES}")
