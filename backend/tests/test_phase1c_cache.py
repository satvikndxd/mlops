"""Phase 1C tests: rate limiting (Redis fallback) and cache no-op safety."""

from __future__ import annotations


def _trace(name: str) -> dict:
    return {"name": name, "agent_name": "a", "spans": []}


def test_rate_limit_returns_429_over_threshold(client, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "rate_limit_per_minute", 3)

    codes = [client.post("/v1/traces", json=_trace(f"r{i}")).status_code for i in range(5)]
    assert codes[:3] == [201, 201, 201]
    assert 429 in codes[3:]


def test_dashboard_works_without_redis(client):
    # With no Redis configured, cache is a no-op and the dashboard still works.
    client.post("/v1/traces", json={
        "name": "x", "agent_name": "a",
        "spans": [{"name": "llm", "kind": "llm", "provider": "openai",
                   "model": "gpt-4o-mini", "input_tokens": 100, "output_tokens": 50}],
    })
    summary = client.get("/v1/dashboard/summary").json()
    assert summary["total_traces"] == 1
