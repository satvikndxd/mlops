"""Authentication, current-user, API-key, and audit-log endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.deps import (
    CurrentPrincipal,
    DbSession,
    get_auth_service,
    require_admin,
)
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import (
    ApiKeyCreate,
    ApiKeyCreated,
    ApiKeyOut,
    AuditLogOut,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from app.services.auth_service import AuthService, Principal

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest, service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    try:
        user = service.register(payload)
    except ValueError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    token, expires_in = service.issue_token(user)
    return TokenResponse(access_token=token, expires_in=expires_in)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    user = service.authenticate(payload.email, payload.password)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    token, expires_in = service.issue_token(user)
    return TokenResponse(access_token=token, expires_in=expires_in)


@router.get("/me", response_model=UserOut, summary="Current authenticated user")
def me(principal: CurrentPrincipal, db: DbSession) -> UserOut:
    if principal.user_id is None:
        # API-key or demo principal — synthesize a lightweight identity.
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Not a user-backed principal")
    user = AuthRepository(db).get_user(principal.user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return UserOut.model_validate(user)


@router.post(
    "/api-keys",
    response_model=ApiKeyCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Create an API key (admin+)",
)
def create_api_key(
    payload: ApiKeyCreate,
    principal: Principal = Depends(require_admin),
    service: AuthService = Depends(get_auth_service),
) -> ApiKeyCreated:
    key, full = service.create_api_key(principal, payload.name)
    return ApiKeyCreated(
        id=key.id,
        name=key.name,
        prefix=key.prefix,
        is_active=key.is_active,
        last_used_at=key.last_used_at,
        created_at=key.created_at,
        api_key=full,
    )


@router.get("/api-keys", response_model=list[ApiKeyOut], summary="List API keys (admin+)")
def list_api_keys(
    principal: Principal = Depends(require_admin),
    service: AuthService = Depends(get_auth_service),
) -> list[ApiKeyOut]:
    return [ApiKeyOut.model_validate(k) for k in service.list_api_keys(principal)]


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(
    key_id: uuid.UUID,
    principal: Principal = Depends(require_admin),
    service: AuthService = Depends(get_auth_service),
) -> Response:
    if not service.revoke_api_key(key_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "API key not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/audit-logs", response_model=list[AuditLogOut], summary="Recent audit logs (admin+)")
def audit_logs(
    db: DbSession,
    principal: Principal = Depends(require_admin),
    limit: int = Query(100, ge=1, le=500),
) -> list[AuditLogOut]:
    org_id = None if principal.actor == "anonymous" else principal.organization_id
    entries = AuthRepository(db).list_audit(org_id, limit=limit)
    return [AuditLogOut.model_validate(e) for e in entries]
