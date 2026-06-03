"""alert rules and alert events (Phase 1B)

Revision ID: 0002_alerts
Revises: 0001_initial
Create Date: 2026-06-03 00:30:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_alerts"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ts(column: str) -> sa.Column:
    return sa.Column(
        column, sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )


def upgrade() -> None:
    op.create_table(
        "alert_rules",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("organization_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("metric", sa.String(length=64), nullable=False),
        sa.Column("comparator", sa.String(length=8), nullable=False, server_default="gt"),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("window_hours", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("severity", sa.String(length=16), nullable=False, server_default="warning"),
        sa.Column("channel", sa.String(length=32), nullable=False, server_default="in_app"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("cooldown_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
        _ts("created_at"),
        _ts("updated_at"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_alert_rules_organization_id", "alert_rules", ["organization_id"])

    op.create_table(
        "alert_events",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("rule_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("organization_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metric", sa.String(length=64), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False, server_default="warning"),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="firing"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["rule_id"], ["alert_rules.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_alert_events_rule_id", "alert_events", ["rule_id"])
    op.create_index("ix_alert_events_organization_id", "alert_events", ["organization_id"])
    op.create_index("ix_alert_events_triggered_at", "alert_events", ["triggered_at"])


def downgrade() -> None:
    op.drop_table("alert_events")
    op.drop_table("alert_rules")
