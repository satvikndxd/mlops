"""Phase 1B tests: alert rule CRUD + evaluation engine (Trace -> Metric -> Alert)."""

from __future__ import annotations


def _trace(name: str, *, status: str = "success") -> dict:
    return {
        "name": name,
        "agent_name": "research-agent",
        "status": status,
        "spans": [
            {
                "name": "llm",
                "kind": "llm",
                "provider": "openai",
                "model": "gpt-4o-mini",
                "input_tokens": 500,
                "output_tokens": 200,
                "latency_ms": 5000.0,
            }
        ],
    }


def test_rule_crud(client):
    rule = client.post(
        "/v1/alerts/rules",
        json={"name": "High failure", "metric": "failure_rate", "comparator": "gt", "threshold": 0.2},
    ).json()
    assert rule["metric"] == "failure_rate"

    rid = rule["id"]
    patched = client.patch(f"/v1/alerts/rules/{rid}", json={"threshold": 0.5, "enabled": False}).json()
    assert patched["threshold"] == 0.5 and patched["enabled"] is False

    assert len(client.get("/v1/alerts/rules").json()) == 1
    assert client.delete(f"/v1/alerts/rules/{rid}").status_code == 204
    assert len(client.get("/v1/alerts/rules").json()) == 0


def test_invalid_metric_rejected(client):
    res = client.post(
        "/v1/alerts/rules",
        json={"name": "bad", "metric": "nonsense", "threshold": 1},
    )
    assert res.status_code == 400


def test_evaluation_fires_when_threshold_breached(client):
    # 2 of 4 traces fail -> failure_rate = 0.5
    for i in range(2):
        client.post("/v1/traces", json=_trace(f"ok#{i}"))
    for i in range(2):
        client.post("/v1/traces", json=_trace(f"bad#{i}", status="failed"))

    client.post(
        "/v1/alerts/rules",
        json={
            "name": "Failure spike",
            "metric": "failure_rate",
            "comparator": "gt",
            "threshold": 0.3,
            "severity": "critical",
            "cooldown_minutes": 0,
        },
    )

    result = client.post("/v1/alerts/evaluate").json()
    assert result["evaluated_rules"] == 1
    assert len(result["fired"]) == 1
    event = result["fired"][0]
    assert event["metric"] == "failure_rate"
    assert event["metric_value"] > 0.3
    assert event["severity"] == "critical"

    events = client.get("/v1/alerts/events").json()
    assert len(events) == 1


def test_evaluation_no_fire_when_within_threshold(client):
    client.post("/v1/traces", json=_trace("ok"))
    client.post(
        "/v1/alerts/rules",
        json={"name": "Latency", "metric": "p95_latency_ms", "comparator": "gt", "threshold": 1e9},
    )
    result = client.post("/v1/alerts/evaluate").json()
    assert len(result["fired"]) == 0


def test_cooldown_suppresses_duplicate(client):
    client.post("/v1/traces", json=_trace("bad", status="failed"))
    client.post(
        "/v1/alerts/rules",
        json={
            "name": "Any failure",
            "metric": "failure_rate",
            "comparator": "gt",
            "threshold": 0.0,
            "cooldown_minutes": 60,
        },
    )
    first = client.post("/v1/alerts/evaluate").json()
    second = client.post("/v1/alerts/evaluate").json()
    assert len(first["fired"]) == 1
    assert len(second["fired"]) == 0  # suppressed by cooldown
