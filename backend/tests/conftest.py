"""Pytest fixtures — isolated SQLite DB and FastAPI test client."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import app.services.audit_service as audit_service
from app.api.deps import get_db
from app.core.config import settings
from app.main import app
from app.models import Base


@pytest.fixture()
def db_session(tmp_path, monkeypatch) -> Iterator[Session]:
    url = f"sqlite:///{tmp_path/'test.db'}"
    engine = create_engine(url, connect_args={"check_same_thread": False}, future=True)
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)

    # Point the audit middleware's standalone session factory at the test DB.
    monkeypatch.setattr(audit_service, "SessionLocal", TestingSession)

    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db_session: Session) -> Iterator[TestClient]:
    def _override() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_enabled(monkeypatch) -> Iterator[None]:
    monkeypatch.setattr(settings, "auth_enabled", True)
    yield
    monkeypatch.setattr(settings, "auth_enabled", False)
