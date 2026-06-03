"""Aggregated v1 API router."""

from fastapi import APIRouter, Depends

from app.api.deps import get_principal
from app.api.v1 import (
    agents,
    alerts,
    auth,
    costs,
    dashboard,
    health,
    monitoring,
    traces,
)

# Data endpoints require an authenticated principal when auth is enabled
# (JWT or API key). health + auth endpoints stay open (login/register/probes).
protected = [Depends(get_principal)]

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(traces.router, prefix="/traces", tags=["traces"], dependencies=protected)
api_router.include_router(
    dashboard.router, prefix="/dashboard", tags=["dashboard"], dependencies=protected
)
api_router.include_router(agents.router, prefix="/agents", tags=["agents"], dependencies=protected)
api_router.include_router(
    monitoring.router, prefix="/monitoring", tags=["monitoring"], dependencies=protected
)
api_router.include_router(costs.router, prefix="/costs", tags=["costs"], dependencies=protected)
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"], dependencies=protected)
