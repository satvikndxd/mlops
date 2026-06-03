"""Aggregated v1 API router."""

from fastapi import APIRouter

from app.api.v1 import agents, dashboard, health, traces

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(traces.router, prefix="/traces", tags=["traces"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
