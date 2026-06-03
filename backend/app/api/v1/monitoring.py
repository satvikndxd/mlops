"""Monitoring endpoints — overview snapshot and metric time-series."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import DbSession
from app.schemas.monitoring import MonitoringOverview, TimeSeries
from app.services.monitoring_service import MonitoringService


def get_monitoring_service(db: DbSession) -> MonitoringService:
    return MonitoringService(db)


router = APIRouter()


@router.get("/overview", response_model=MonitoringOverview, summary="Monitoring snapshot")
def overview(
    window_hours: int = Query(24, ge=1, le=24 * 90),
    service: MonitoringService = Depends(get_monitoring_service),
) -> MonitoringOverview:
    return service.overview(window_hours=window_hours)


@router.get("/timeseries", response_model=TimeSeries, summary="Metric time-series")
def timeseries(
    metric: str = Query("volume"),
    hours: int = Query(168, ge=1, le=24 * 365),
    bucket: str = Query("day", pattern="^(hour|day)$"),
    service: MonitoringService = Depends(get_monitoring_service),
) -> TimeSeries:
    try:
        return service.timeseries(metric=metric, hours=hours, bucket=bucket)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
