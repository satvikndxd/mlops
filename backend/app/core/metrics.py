"""Prometheus metrics — HTTP middleware and domain counters.

Exposes a registry-backed ``/metrics`` endpoint and helper functions the
service layer calls to record domain events (traces, tokens, cost, failures).
"""

from __future__ import annotations

import time

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.requests import Request
from starlette.responses import Response

# A dedicated registry keeps AgentForge metrics isolated and testable.
REGISTRY = CollectorRegistry()

# --- HTTP metrics ------------------------------------------------------
HTTP_REQUESTS = Counter(
    "agentforge_http_requests_total",
    "Total HTTP requests.",
    ["method", "path", "status"],
    registry=REGISTRY,
)
HTTP_LATENCY = Histogram(
    "agentforge_http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    registry=REGISTRY,
)

# --- Domain metrics ----------------------------------------------------
TRACES_INGESTED = Counter(
    "agentforge_traces_ingested_total",
    "Total traces ingested.",
    ["agent", "status"],
    registry=REGISTRY,
)
TRACE_LATENCY = Histogram(
    "agentforge_trace_latency_ms",
    "Agent run latency in milliseconds.",
    buckets=(50, 100, 250, 500, 1000, 2500, 5000, 10000, 30000),
    registry=REGISTRY,
)
LLM_TOKENS = Counter(
    "agentforge_llm_tokens_total",
    "Total LLM tokens processed.",
    ["provider", "direction"],
    registry=REGISTRY,
)
LLM_COST = Counter(
    "agentforge_llm_cost_usd_total",
    "Total LLM cost in USD.",
    ["provider"],
    registry=REGISTRY,
)
TOOL_CALLS = Counter(
    "agentforge_tool_calls_total",
    "Total tool calls.",
    ["status"],
    registry=REGISTRY,
)
ACTIVE_AGENTS = Gauge(
    "agentforge_active_agents",
    "Number of distinct agents seen.",
    registry=REGISTRY,
)


def record_trace_metrics(
    *,
    agent: str,
    status: str,
    latency_ms: float,
    cost_by_provider: dict[str, float],
    tokens_by_provider: dict[str, tuple[int, int]],
    tool_statuses: list[str],
) -> None:
    TRACES_INGESTED.labels(agent=agent, status=status).inc()
    TRACE_LATENCY.observe(max(latency_ms, 0.0))
    for provider, cost in cost_by_provider.items():
        if cost:
            LLM_COST.labels(provider=provider).inc(cost)
    for provider, (inp, out) in tokens_by_provider.items():
        if inp:
            LLM_TOKENS.labels(provider=provider, direction="input").inc(inp)
        if out:
            LLM_TOKENS.labels(provider=provider, direction="output").inc(out)
    for tool_status in tool_statuses:
        TOOL_CALLS.labels(status=tool_status).inc()


def metrics_response() -> Response:
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


def _normalize_path(request: Request) -> str:
    """Use the route template (e.g. /v1/traces/{trace_id}) to avoid label explosion."""
    route = request.scope.get("route")
    if route is not None and getattr(route, "path", None):
        return route.path
    return request.url.path


async def prometheus_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    path = _normalize_path(request)
    if path != "/metrics":
        elapsed = time.perf_counter() - start
        HTTP_LATENCY.labels(request.method, path).observe(elapsed)
        HTTP_REQUESTS.labels(request.method, path, str(response.status_code)).inc()
    return response
