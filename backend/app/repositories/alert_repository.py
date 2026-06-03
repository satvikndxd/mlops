"""Data access for alert rules and events."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models import AlertEvent, AlertRule
from app.repositories.base import BaseRepository


class AlertRepository(BaseRepository):
    # --- Rules ---------------------------------------------------------
    def add_rule(self, rule: AlertRule) -> AlertRule:
        self.db.add(rule)
        self.db.flush()
        return rule

    def get_rule(self, rule_id: uuid.UUID) -> AlertRule | None:
        return self.db.get(AlertRule, rule_id)

    def list_rules(self, organization_id: uuid.UUID, enabled_only: bool = False) -> list[AlertRule]:
        stmt = select(AlertRule).where(AlertRule.organization_id == organization_id)
        if enabled_only:
            stmt = stmt.where(AlertRule.enabled.is_(True))
        return list(self.db.scalars(stmt.order_by(AlertRule.created_at.desc())))

    def delete_rule(self, rule: AlertRule) -> None:
        self.db.delete(rule)
        self.db.flush()

    # --- Events --------------------------------------------------------
    def add_event(self, event: AlertEvent) -> AlertEvent:
        self.db.add(event)
        self.db.flush()
        return event

    def list_events(self, organization_id: uuid.UUID, limit: int = 100) -> list[AlertEvent]:
        return list(
            self.db.scalars(
                select(AlertEvent)
                .where(AlertEvent.organization_id == organization_id)
                .order_by(AlertEvent.triggered_at.desc())
                .limit(limit)
            )
        )
