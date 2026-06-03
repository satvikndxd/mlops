"""Phase 1A tests: Prometheus metrics, monitoring, cost analytics."""

from __future__ import annotations


def _trace(name: str, *, status: str = "success", tool_status: str = "success") -> dict:
    return {
        "name": name,
        "agent_name": "research-agent",
        "framework": "langchain",
        "model": "gpt-4o-mini",
        "status": status,
        "user_email": "demo@agentforge.dev",
        "spans": [
            {
                "name": "llm:gpt-4o-mini",
                "kind": "llm",
                "provider": "openai",
                "model": "gpt-4o-mini",
                "input_tokens": 1000,
                "output_tokens": 500,
                "latency_ms": 300.0,
            },
            {
                "name": "tool:web_search",
                "kind": "tool",
                "status": tool_status,
                "latency_ms": 120.0,
                "parent_index": 0,
            },
        ],
    }


def _seed(client, n=5):
    for i in range(n):
        client.post("/v1/traces", json=_trace(f"run#{i}"))


def test_metrics_endpoint_exposes_prometheus(client):
    client.post("/v1/traces", json=_trace("run#metrics"))
    res = client.get("/metrics")
    assert res.status_code == 200
    body = res.text
    assert "agentforge_traces_ingested_total" in body
    assert "agentforge_llm_cost_usd_total" in body
    assert "agentforge_http_requests_total" in body


def test_monitoring_overview(client):
    _seed(client, 5)
    client.post("/v1/traces", json=_trace("failed#1", status="failed"))
    ov = client.get("/v1/monitoring/overview?window_hours=24").json()
    assert ov["total_traces"] == 6
    assert 0 < ov["success_rate"] < 1
    assert ov["failure_rate"] > 0
    assert ov["p95_latency_ms"] >= ov["p50_latency_ms"]
    assert ov["tool_success_rate"] == 1.0
    assert ov["total_tokens"] == 6 * 1500


def test_monitoring_timeseries(client):
    _seed(client, 3)
    ts = client.get("/v1/monitoring/timeseries?metric=cost&hours=48&bucket=day").json()
    assert ts["metric"] == "cost"
    assert len(ts["points"]) >= 1
    assert sum(p["value"] for p in ts["points"]) > 0


def test_monitoring_timeseries_rejects_bad_metric(client):
    assert client.get("/v1/monitoring/timeseries?metric=bogus").status_code == 400


def test_cost_analytics(client):
    _seed(client, 4)
    summary = client.get("/v1/costs/summary").json()
    assert summary["all_time"] > 0
    assert summary["this_month"] >= summary["today"] - 1e-9

    by_provider = client.get("/v1/costs/by-provider").json()
    assert any(item["key"] == "openai" for item in by_provider)

    by_agent = client.get("/v1/costs/by-agent").json()
    assert by_agent[0]["key"] == "research-agent"

    by_model = client.get("/v1/costs/by-model").json()
    assert any(item["key"] == "gpt-4o-mini" for item in by_model)

    by_user = client.get("/v1/costs/by-user").json()
    assert any(item["key"] == "demo@agentforge.dev" for item in by_user)

    assert client.get("/v1/costs/daily").json()
    assert client.get("/v1/costs/monthly").json()
