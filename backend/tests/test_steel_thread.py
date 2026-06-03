"""End-to-end steel-thread tests: ingest → store → cost → dashboard."""

from __future__ import annotations

from app.integrations.pricing import compute_cost


def _sample_trace() -> dict:
    return {
        "name": "answer_question#1",
        "agent_name": "research-agent",
        "framework": "langchain",
        "model": "gpt-4o-mini",
        "status": "success",
        "user_email": "demo@agentforge.dev",
        "spans": [
            {
                "name": "llm:gpt-4o-mini",
                "kind": "llm",
                "provider": "openai",
                "model": "gpt-4o-mini",
                "operation": "chat",
                "input_tokens": 1000,
                "output_tokens": 500,
                "latency_ms": 420.0,
            },
            {
                "name": "tool:web_search",
                "kind": "tool",
                "operation": "execute_tool",
                "latency_ms": 150.0,
                "parent_index": 0,
            },
        ],
    }


def test_healthz(client):
    assert client.get("/healthz").json()["status"] == "ok"
    assert client.get("/v1/readyz").json()["database"] == "ok"


def test_ingest_computes_cost_and_persists(client):
    resp = client.post("/v1/traces", json=_sample_trace())
    assert resp.status_code == 201, resp.text
    body = resp.json()

    expected = float(compute_cost("openai", "gpt-4o-mini", 1000, 500))
    assert body["total_tokens"] == 1500
    assert body["span_count"] == 2
    assert abs(body["total_cost"] - expected) < 1e-9
    assert expected > 0

    trace_id = body["trace_id"]
    detail = client.get(f"/v1/traces/{trace_id}").json()
    assert detail["name"] == "answer_question#1"
    assert len(detail["spans"]) == 2
    # Execution graph: the tool span points at the llm span.
    llm_span = next(s for s in detail["spans"] if s["kind"] == "llm")
    tool_span = next(s for s in detail["spans"] if s["kind"] == "tool")
    assert tool_span["parent_span_id"] == llm_span["id"]


def test_dashboard_summary_reflects_ingest(client):
    client.post("/v1/traces", json=_sample_trace())
    client.post("/v1/traces", json=_sample_trace())

    summary = client.get("/v1/dashboard/summary").json()
    assert summary["total_traces"] == 2
    assert summary["total_tokens"] == 3000
    assert summary["total_cost"] > 0
    assert summary["active_agents"] == 1
    assert any(p["provider"] == "openai" for p in summary["cost_by_provider"])
    assert len(summary["recent_traces"]) == 2


def test_agents_listed_after_ingest(client):
    client.post("/v1/traces", json=_sample_trace())
    agents = client.get("/v1/agents").json()
    assert [a["name"] for a in agents] == ["research-agent"]


def test_unknown_trace_returns_404(client):
    import uuid

    assert client.get(f"/v1/traces/{uuid.uuid4()}").status_code == 404
