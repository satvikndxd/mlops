"""Dashboard summary endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_dashboard_service
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary, summary="Dashboard summary metrics")
def dashboard_summary(
    recent_limit: int = Query(10, ge=1, le=100),
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardSummary:
    return service.summary(recent_limit=recent_limit)
