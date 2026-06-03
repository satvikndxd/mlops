"""Alert rule CRUD, evaluation, and event endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.deps import DbSession, require_admin
from app.schemas.alert import (
    AlertEventOut,
    AlertRuleCreate,
    AlertRuleOut,
    AlertRuleUpdate,
    EvaluateResult,
)
from app.services.alert_service import AlertService


def get_alert_service(db: DbSession) -> AlertService:
    return AlertService(db)


router = APIRouter()


@router.post(
    "/rules",
    response_model=AlertRuleOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_rule(
    payload: AlertRuleCreate, service: AlertService = Depends(get_alert_service)
) -> AlertRuleOut:
    try:
        rule = service.create_rule(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return AlertRuleOut.model_validate(rule)


@router.get("/rules", response_model=list[AlertRuleOut], summary="List alert rules")
def list_rules(service: AlertService = Depends(get_alert_service)) -> list[AlertRuleOut]:
    return [AlertRuleOut.model_validate(r) for r in service.list_rules()]


@router.patch(
    "/rules/{rule_id}",
    response_model=AlertRuleOut,
    summary="Update an alert rule",
    dependencies=[Depends(require_admin)],
)
def update_rule(
    rule_id: uuid.UUID,
    payload: AlertRuleUpdate,
    service: AlertService = Depends(get_alert_service),
) -> AlertRuleOut:
    try:
        rule = service.update_rule(rule_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    return AlertRuleOut.model_validate(rule)


@router.delete(
    "/rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_rule(
    rule_id: uuid.UUID, service: AlertService = Depends(get_alert_service)
) -> Response:
    if not service.delete_rule(rule_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/evaluate", response_model=EvaluateResult, summary="Evaluate all rules now")
def evaluate(service: AlertService = Depends(get_alert_service)) -> EvaluateResult:
    fired = service.evaluate()
    return EvaluateResult(
        evaluated_rules=len(service.list_rules()),
        fired=[AlertEventOut.model_validate(e) for e in fired],
    )


@router.get("/events", response_model=list[AlertEventOut], summary="Recent alert events")
def list_events(
    limit: int = Query(100, ge=1, le=500),
    service: AlertService = Depends(get_alert_service),
) -> list[AlertEventOut]:
    return [AlertEventOut.model_validate(e) for e in service.list_events(limit=limit)]
