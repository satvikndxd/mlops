"""Data access for users, API keys, and audit logs."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select

from app.models import ApiKey, AuditLog, Organization, User
from app.repositories.base import BaseRepository


class AuthRepository(BaseRepository):
    # --- Organizations / users ----------------------------------------
    def create_organization(self, name: str, slug: str) -> Organization:
        org = Organization(name=name, slug=slug)
        self.db.add(org)
        self.db.flush()
        return org

    def get_org_by_slug(self, slug: str) -> Organization | None:
        return self.db.scalar(select(Organization).where(Organization.slug == slug))

    def get_user_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def get_user(self, user_id: uuid.UUID) -> User | None:
        return self.db.get(User, user_id)

    def add_user(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user

    def count_users(self) -> int:
        return int(self.db.scalar(select(func.count(User.id))) or 0)

    # --- API keys ------------------------------------------------------
    def add_api_key(self, key: ApiKey) -> ApiKey:
        self.db.add(key)
        self.db.flush()
        return key

    def get_api_key_by_hash(self, hashed_key: str) -> ApiKey | None:
        return self.db.scalar(
            select(ApiKey).where(ApiKey.hashed_key == hashed_key, ApiKey.is_active.is_(True))
        )

    def list_api_keys(self, organization_id: uuid.UUID) -> list[ApiKey]:
        return list(
            self.db.scalars(
                select(ApiKey)
                .where(ApiKey.organization_id == organization_id)
                .order_by(ApiKey.created_at.desc())
            )
        )

    def get_api_key(self, key_id: uuid.UUID) -> ApiKey | None:
        return self.db.get(ApiKey, key_id)

    # --- Audit ---------------------------------------------------------
    def add_audit(self, entry: AuditLog) -> None:
        self.db.add(entry)

    def list_audit(self, organization_id: uuid.UUID | None, limit: int = 100) -> list[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        if organization_id is not None:
            stmt = stmt.where(AuditLog.organization_id == organization_id)
        return list(self.db.scalars(stmt))
