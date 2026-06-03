"""Shared FastAPI dependencies (dependency injection wiring + RBAC)."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.repositories.agent_repository import AgentRepository
from app.services.auth_service import AuthService, Principal
from app.services.dashboard_service import DashboardService
from app.services.ingest_service import IngestService

DbSession = Annotated[Session, Depends(get_db)]


def get_ingest_service(db: DbSession) -> IngestService:
    return IngestService(db)


def get_dashboard_service(db: DbSession) -> DashboardService:
    return DashboardService(db)


def get_auth_service(db: DbSession) -> AuthService:
    return AuthService(db)


def get_principal(
    db: DbSession,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
) -> Principal:
    """Resolve the calling principal.

    When ``auth_enabled`` is False (demo default) this returns an owner-level
    principal bound to the default organization so the public dashboard and SDK
    ingest work without credentials. When True, a valid JWT or API key is
    required.
    """
    auth = AuthService(db)

    if authorization and authorization.lower().startswith("bearer "):
        claims = decode_access_token(authorization.split(" ", 1)[1])
        if claims:
            principal = auth.principal_from_jwt_claims(claims)
            if principal:
                return principal
        if settings.auth_enabled:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")

    if x_api_key:
        principal = auth.principal_from_api_key(x_api_key)
        if principal:
            return principal
        if settings.auth_enabled:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")

    if settings.auth_enabled:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Demo mode: behave as the default-org owner.
    org = AgentRepository(db).get_or_create_default_org()
    return Principal(organization_id=org.id, actor="anonymous", role="owner")


CurrentPrincipal = Annotated[Principal, Depends(get_principal)]


def require_role(minimum: str):
    """Dependency factory enforcing a minimum role (no-op when auth disabled)."""

    def _dep(principal: CurrentPrincipal) -> Principal:
        if settings.auth_enabled and not principal.has_role(minimum):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Requires '{minimum}' role or higher (you are '{principal.role}').",
            )
        return principal

    return _dep


require_viewer = require_role("viewer")
require_member = require_role("member")
require_admin = require_role("admin")
