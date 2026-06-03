"""Data access for organizations, agents, agent versions, and users."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.core.config import settings
from app.models import Agent, AgentVersion, Organization, User
from app.repositories.base import BaseRepository


class AgentRepository(BaseRepository):
    # --- Organizations -------------------------------------------------
    def get_or_create_default_org(self) -> Organization:
        org = self.db.scalar(
            select(Organization).where(Organization.slug == settings.default_org_slug)
        )
        if org is None:
            org = Organization(name=settings.default_org_name, slug=settings.default_org_slug)
            self.db.add(org)
            self.db.flush()
        return org

    # --- Agents --------------------------------------------------------
    def get_or_create_agent(
        self, organization_id: uuid.UUID, name: str, framework: str | None
    ) -> Agent:
        agent = self.db.scalar(
            select(Agent).where(
                Agent.organization_id == organization_id, Agent.name == name
            )
        )
        if agent is None:
            agent = Agent(organization_id=organization_id, name=name, framework=framework)
            self.db.add(agent)
            self.db.flush()
        elif framework and not agent.framework:
            agent.framework = framework
        return agent

    def list_agents(self, organization_id: uuid.UUID) -> list[Agent]:
        return list(
            self.db.scalars(
                select(Agent)
                .where(Agent.organization_id == organization_id)
                .order_by(Agent.name)
            )
        )

    def get_agent(self, agent_id: uuid.UUID) -> Agent | None:
        return self.db.get(Agent, agent_id)

    def count_agents(self, organization_id: uuid.UUID) -> int:
        return len(self.list_agents(organization_id))

    # --- Versions ------------------------------------------------------
    def get_or_create_version(
        self, agent: Agent, version: int | None, model: str | None
    ) -> AgentVersion:
        target = version or 1
        existing = self.db.scalar(
            select(AgentVersion).where(
                AgentVersion.agent_id == agent.id, AgentVersion.version == target
            )
        )
        if existing is None:
            existing = AgentVersion(agent_id=agent.id, version=target, model=model)
            self.db.add(existing)
            self.db.flush()
        elif model and not existing.model:
            existing.model = model
        return existing

    # --- Users ---------------------------------------------------------
    def get_user_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def get_or_create_user(self, organization_id: uuid.UUID, email: str) -> User:
        user = self.get_user_by_email(email)
        if user is None:
            user = User(organization_id=organization_id, email=email, role="member")
            self.db.add(user)
            self.db.flush()
        return user
