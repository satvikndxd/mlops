"""initial schema — steel thread (organizations, users, agents, traces, spans, costs)

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-03 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ts(column: str) -> sa.Column:
    return sa.Column(
        column, sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        _ts("created_at"),
        _ts("updated_at"),
        sa.UniqueConstraint("slug", name="uq_organizations_slug"),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"])

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("organization_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("role", sa.String(length=32), nullable=False, server_default="member"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        _ts("created_at"),
        _ts("updated_at"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_organization_id", "users", ["organization_id"])

    op.create_table(
        "agents",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("organization_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("framework", sa.String(length=64), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        _ts("created_at"),
        _ts("updated_at"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("organization_id", "name", name="uq_agent_org_name"),
    )
    op.create_index("ix_agents_organization_id", "agents", ["organization_id"])

    op.create_table(
        "agent_versions",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("agent_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("prompt", sa.Text(), nullable=True),
        sa.Column("tools", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        _ts("created_at"),
        _ts("updated_at"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("agent_id", "version", name="uq_version_agent_num"),
    )
    op.create_index("ix_agent_versions_agent_id", "agent_versions", ["agent_id"])

    op.create_table(
        "traces",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("organization_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("agent_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("agent_version_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="success"),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_cost", sa.Numeric(14, 6), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        _ts("created_at"),
        _ts("updated_at"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_version_id"], ["agent_versions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_traces_organization_id", "traces", ["organization_id"])
    op.create_index("ix_traces_agent_id", "traces", ["agent_id"])
    op.create_index("ix_traces_status", "traces", ["status"])

    op.create_table(
        "spans",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("trace_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("parent_span_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False, server_default="llm"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="success"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("gen_ai_system", sa.String(length=64), nullable=True),
        sa.Column("gen_ai_request_model", sa.String(length=128), nullable=True),
        sa.Column("gen_ai_operation", sa.String(length=64), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("cost", sa.Numeric(14, 6), nullable=False, server_default="0"),
        sa.Column("attributes", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["trace_id"], ["traces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_span_id"], ["spans.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_spans_trace_id", "spans", ["trace_id"])
    op.create_index("ix_spans_kind", "spans", ["kind"])

    op.create_table(
        "cost_records",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("trace_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("organization_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost", sa.Numeric(14, 6), nullable=False, server_default="0"),
        sa.Column("day", sa.Date(), nullable=False),
        _ts("created_at"),
        _ts("updated_at"),
        sa.ForeignKeyConstraint(["trace_id"], ["traces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_cost_records_trace_id", "cost_records", ["trace_id"])
    op.create_index("ix_cost_records_organization_id", "cost_records", ["organization_id"])
    op.create_index("ix_cost_records_provider", "cost_records", ["provider"])
    op.create_index("ix_cost_records_day", "cost_records", ["day"])


def downgrade() -> None:
    op.drop_table("cost_records")
    op.drop_table("spans")
    op.drop_table("traces")
    op.drop_table("agent_versions")
    op.drop_table("agents")
    op.drop_table("users")
    op.drop_table("organizations")
