"""Agent and AgentVersion models (registry foundation)."""

from __future__ import annotations

import uuid

from sqlalchemy import JSON, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Agent(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "agents"
    __table_args__ = (UniqueConstraint("organization_id", "name", name="uq_agent_org_name"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    framework: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization: Mapped["Organization"] = relationship(back_populates="agents")  # noqa: F821
    versions: Mapped[list["AgentVersion"]] = relationship(
        back_populates="agent", cascade="all, delete-orphan"
    )
    traces: Mapped[list["Trace"]] = relationship(  # noqa: F821
        back_populates="agent", cascade="all, delete-orphan"
    )


class AgentVersion(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "agent_versions"
    __table_args__ = (UniqueConstraint("agent_id", "version", name="uq_version_agent_num"),)

    agent_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    tools: Mapped[list | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")

    agent: Mapped["Agent"] = relationship(back_populates="versions")
