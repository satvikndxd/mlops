"""Trace ingestion and read endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import DbSession, get_ingest_service, rate_limit
from app.repositories.agent_repository import AgentRepository
from app.repositories.trace_repository import TraceRepository
from app.schemas.trace import (
    TraceDetail,
    TraceIn,
    TraceIngestResult,
    TraceSummary,
)
from app.services.ingest_service import IngestService

router = APIRouter()


@router.post(
    "",
    response_model=TraceIngestResult,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest an agent trace",
    dependencies=[Depends(rate_limit)],
)
def ingest_trace(
    payload: TraceIn,
    service: IngestService = Depends(get_ingest_service),
) -> TraceIngestResult:
    trace = service.ingest(payload)
    return TraceIngestResult(
        trace_id=trace.id,
        total_cost=float(trace.total_cost),
        total_tokens=trace.total_tokens,
        span_count=len(trace.spans),
    )


@router.get("", response_model=list[TraceSummary], summary="List recent traces")
def list_traces(
    db: DbSession,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> list[TraceSummary]:
    org = AgentRepository(db).get_or_create_default_org()
    traces = TraceRepository(db).list_recent(org.id, limit=limit, offset=offset)
    return [TraceSummary.model_validate(t) for t in traces]


@router.get("/{trace_id}", response_model=TraceDetail, summary="Get a trace with spans (replay)")
def get_trace(trace_id: uuid.UUID, db: DbSession) -> TraceDetail:
    trace = TraceRepository(db).get(trace_id)
    if trace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trace not found")
    return TraceDetail.model_validate(trace)
