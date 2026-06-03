"""Cost analytics endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import DbSession
from app.schemas.cost import CostBreakdownItem, CostSummary, DailyCost, MonthCost
from app.services.cost_service import CostService


def get_cost_service(db: DbSession) -> CostService:
    return CostService(db)


router = APIRouter()


@router.get("/summary", response_model=CostSummary, summary="Today / month / all-time spend")
def summary(service: CostService = Depends(get_cost_service)) -> CostSummary:
    return service.summary()


@router.get("/by-provider", response_model=list[CostBreakdownItem], summary="Spend by provider")
def by_provider(service: CostService = Depends(get_cost_service)) -> list[CostBreakdownItem]:
    return service.by_provider()


@router.get("/by-model", response_model=list[CostBreakdownItem], summary="Spend by model")
def by_model(service: CostService = Depends(get_cost_service)) -> list[CostBreakdownItem]:
    return service.by_model()


@router.get("/by-agent", response_model=list[CostBreakdownItem], summary="Spend by agent")
def by_agent(service: CostService = Depends(get_cost_service)) -> list[CostBreakdownItem]:
    return service.by_agent()


@router.get("/by-user", response_model=list[CostBreakdownItem], summary="Spend by user")
def by_user(service: CostService = Depends(get_cost_service)) -> list[CostBreakdownItem]:
    return service.by_user()


@router.get("/daily", response_model=list[DailyCost], summary="Daily spend series")
def daily(service: CostService = Depends(get_cost_service)) -> list[DailyCost]:
    return service.daily()


@router.get("/monthly", response_model=list[MonthCost], summary="Monthly spend series")
def monthly(service: CostService = Depends(get_cost_service)) -> list[MonthCost]:
    return service.monthly()
