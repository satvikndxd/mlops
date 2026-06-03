"""Phase 1C tests: JWT auth, RBAC, API keys, and audit logging."""

from __future__ import annotations

from app.core.security import create_access_token, hash_password
from app.models import User


def _register(client, email="owner@acme.dev"):
    return client.post(
        "/v1/auth/register",
        json={"email": email, "password": "supersecret123", "organization_name": "Acme"},
    )


def test_register_login_me(client):
    res = _register(client)
    assert res.status_code == 201, res.text
    token = res.json()["access_token"]

    # login
    login = client.post(
        "/v1/auth/login", json={"email": "owner@acme.dev", "password": "supersecret123"}
    )
    assert login.status_code == 200

    me = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "owner@acme.dev"
    assert me.json()["role"] == "owner"


def test_login_rejects_bad_password(client):
    _register(client)
    res = client.post(
        "/v1/auth/login", json={"email": "owner@acme.dev", "password": "wrong"}
    )
    assert res.status_code == 401


def test_duplicate_registration_conflicts(client):
    _register(client)
    assert _register(client).status_code == 409


def test_auth_required_when_enabled(client, auth_enabled):
    # No credentials -> 401
    assert client.get("/v1/traces").status_code == 401
    # With a valid token -> 200
    token = _register(client).json()["access_token"]
    assert client.get("/v1/traces", headers={"Authorization": f"Bearer {token}"}).status_code == 200


def test_rbac_blocks_viewer_from_creating_rules(client, db_session, auth_enabled):
    # Owner can create a rule.
    owner_token = _register(client).json()["access_token"]
    rule_body = {"name": "r", "metric": "failure_rate", "comparator": "gt", "threshold": 0.1}
    ok = client.post(
        "/v1/alerts/rules", json=rule_body, headers={"Authorization": f"Bearer {owner_token}"}
    )
    assert ok.status_code == 201

    # A viewer cannot.
    viewer = User(
        organization_id=db_session.scalar(__import__("sqlalchemy").select(User.organization_id)),
        email="viewer@acme.dev",
        hashed_password=hash_password("supersecret123"),
        role="viewer",
    )
    db_session.add(viewer)
    db_session.commit()
    viewer_token = create_access_token(str(viewer.id))
    forbidden = client.post(
        "/v1/alerts/rules", json=rule_body, headers={"Authorization": f"Bearer {viewer_token}"}
    )
    assert forbidden.status_code == 403


def test_api_key_lifecycle_and_ingest(client, auth_enabled):
    token = _register(client).json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}

    created = client.post("/v1/auth/api-keys", json={"name": "ci"}, headers=auth)
    assert created.status_code == 201
    full_key = created.json()["api_key"]
    assert full_key.startswith("af_")

    # Ingest using the API key (no JWT).
    trace = {
        "name": "via_api_key",
        "agent_name": "research-agent",
        "spans": [
            {"name": "llm", "kind": "llm", "provider": "openai", "model": "gpt-4o-mini",
             "input_tokens": 100, "output_tokens": 50, "latency_ms": 100}
        ],
    }
    ok = client.post("/v1/traces", json=trace, headers={"X-API-Key": full_key})
    assert ok.status_code == 201

    # An invalid key is rejected.
    bad = client.post("/v1/traces", json=trace, headers={"X-API-Key": "af_invalid"})
    assert bad.status_code == 401


def test_audit_log_records_mutations(client):
    # Demo mode (no auth): a trace ingest is a mutation and should be audited.
    client.post(
        "/v1/traces",
        json={"name": "audited", "agent_name": "a", "spans": []},
    )
    logs = client.get("/v1/auth/audit-logs").json()
    assert any(e["resource"] == "/v1/traces" and e["action"] == "POST" for e in logs)
