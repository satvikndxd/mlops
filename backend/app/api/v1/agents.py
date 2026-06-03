"""Agent read endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict

from app.api.deps import DbSession
from app.repositories.agent_repository import AgentRepository


class AgentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    framework: str | None
    description: str | None


router = APIRouter()


@router.get("", response_model=list[AgentOut], summary="List agents")
def list_agents(db: DbSession) -> list[AgentOut]:
    repo = AgentRepository(db)
    org = repo.get_or_create_default_org()
    return [AgentOut.model_validate(a) for a in repo.list_agents(org.id)]


@router.get("/{agent_id}", response_model=AgentOut, summary="Get an agent")
def get_agent(agent_id: uuid.UUID, db: DbSession) -> AgentOut:
    agent = AgentRepository(db).get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return AgentOut.model_validate(agent)
