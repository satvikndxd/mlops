"""Authentication / authorization service.

Handles registration, login (JWT), API-key issuance/verification, and the
principal model used for RBAC. The first user to register an organization
becomes its ``owner``; subsequent users default to ``member``.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_api_key,
    hash_api_key,
    hash_password,
    verify_password,
)
from app.models import ApiKey, User
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import RegisterRequest

ROLE_RANK = {"viewer": 0, "service": 1, "member": 1, "admin": 2, "owner": 3}


@dataclass
class Principal:
    organization_id: uuid.UUID
    actor: str
    role: str
    user_id: uuid.UUID | None = None

    def has_role(self, minimum: str) -> bool:
        return ROLE_RANK.get(self.role, -1) >= ROLE_RANK.get(minimum, 99)


def _slugify(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "org"
    return base[:48]


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AuthRepository(db)

    # --- Registration / login -----------------------------------------
    def register(self, payload: RegisterRequest) -> User:
        if self.repo.get_user_by_email(payload.email):
            raise ValueError("A user with that email already exists.")

        org_name = payload.organization_name or f"{payload.email.split('@')[0]}'s org"
        slug = self._unique_slug(_slugify(org_name))
        org = self.repo.create_organization(org_name, slug)

        user = User(
            organization_id=org.id,
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
            role="owner",
        )
        self.repo.add_user(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate(self, email: str, password: str) -> User | None:
        user = self.repo.get_user_by_email(email)
        if user and user.is_active and verify_password(password, user.hashed_password):
            return user
        return None

    def issue_token(self, user: User) -> tuple[str, int]:
        token = create_access_token(
            str(user.id),
            extra={"email": user.email, "role": user.role, "org": str(user.organization_id)},
        )
        return token, settings.access_token_expire_minutes * 60

    def _unique_slug(self, base: str) -> str:
        slug = base
        i = 1
        while self.repo.get_org_by_slug(slug) is not None:
            i += 1
            slug = f"{base}-{i}"
        return slug

    # --- API keys ------------------------------------------------------
    def create_api_key(self, principal: Principal, name: str) -> tuple[ApiKey, str]:
        full, prefix, hashed = generate_api_key()
        key = ApiKey(
            organization_id=principal.organization_id,
            name=name,
            prefix=prefix,
            hashed_key=hashed,
            created_by=principal.user_id,
        )
        self.repo.add_api_key(key)
        self.db.commit()
        self.db.refresh(key)
        return key, full

    def list_api_keys(self, principal: Principal) -> list[ApiKey]:
        return self.repo.list_api_keys(principal.organization_id)

    def revoke_api_key(self, key_id: uuid.UUID) -> bool:
        key = self.repo.get_api_key(key_id)
        if key is None:
            return False
        key.is_active = False
        self.db.commit()
        return True

    # --- Principal resolution -----------------------------------------
    def principal_from_jwt_claims(self, claims: dict) -> Principal | None:
        user_id = claims.get("sub")
        if not user_id:
            return None
        try:
            user = self.repo.get_user(uuid.UUID(user_id))
        except (ValueError, TypeError):
            return None
        if user is None or not user.is_active:
            return None
        return Principal(
            organization_id=user.organization_id,
            actor=user.email,
            role=user.role,
            user_id=user.id,
        )

    def principal_from_api_key(self, full_key: str) -> Principal | None:
        key = self.repo.get_api_key_by_hash(hash_api_key(full_key))
        if key is None:
            return None
        key.last_used_at = datetime.now(timezone.utc)
        self.db.commit()
        return Principal(
            organization_id=key.organization_id,
            actor=f"apikey:{key.prefix}",
            role="service",
        )
