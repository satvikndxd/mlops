"""Shared FastAPI dependencies (dependency injection wiring)."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.dashboard_service import DashboardService
from app.services.ingest_service import IngestService

DbSession = Annotated[Session, Depends(get_db)]


def get_ingest_service(db: DbSession) -> IngestService:
    return IngestService(db)


def get_dashboard_service(db: DbSession) -> DashboardService:
    return DashboardService(db)
