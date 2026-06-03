"""Audit logging — records mutating API calls (best-effort, never blocks requests)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from starlette.requests import Request
from starlette.responses import Response

from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.core.security import decode_access_token
from app.models import AuditLog

logger = get_logger("audit")

_MUTATING = {"POST", "PUT", "PATCH", "DELETE"}


def _actor_and_org(request: Request) -> tuple[str, uuid.UUID | None]:
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        claims = decode_access_token(auth.split(" ", 1)[1])
        if claims:
            org = claims.get("org")
            try:
                org_id = uuid.UUID(org) if org else None
            except (ValueError, TypeError):
                org_id = None
            return claims.get("email", "user"), org_id
    if request.headers.get("x-api-key"):
        return "apikey", None
    return "anonymous", None


def record_audit(request: Request, response: Response) -> None:
    if request.method not in _MUTATING:
        return
    path = request.url.path
    if not path.startswith("/v1"):
        return

    actor, org_id = _actor_and_org(request)
    db = SessionLocal()
    try:
        db.add(
            AuditLog(
                organization_id=org_id,
                actor=actor,
                action=request.method,
                resource=path,
                status_code=response.status_code,
                ip=request.client.host if request.client else None,
                created_at=datetime.now(timezone.utc),
            )
        )
        db.commit()
    except Exception as exc:  # pragma: no cover - audit must never break a request
        db.rollback()
        logger.warning("audit log failed: %s", exc)
    finally:
        db.close()
