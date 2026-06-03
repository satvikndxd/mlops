"""Health and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DbSession

router = APIRouter()


@router.get("/healthz", summary="Liveness probe")
def healthz() -> dict:
    return {"status": "ok"}


@router.get("/readyz", summary="Readiness probe (checks DB)")
def readyz(db: DbSession) -> dict:
    db.execute(text("SELECT 1"))
    return {"status": "ready", "database": "ok"}
