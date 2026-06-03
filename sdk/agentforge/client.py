"""AgentForge SDK client — emit agent traces to an AgentForge backend.

Zero hard dependencies (uses the standard library) so it drops into any agent
runtime. Spans carry OpenTelemetry GenAI semantic-convention attributes.

Example
-------
    from agentforge import AgentForge

    af = AgentForge(agent_name="research-agent", framework="langchain")
    with af.trace("answer_question") as run:
        run.llm("gpt-4o-mini", input_tokens=1200, output_tokens=320,
                provider="openai", prompt="...", completion="...")
        run.tool("web_search", args={"q": "agentops"}, output={"hits": 5},
                 latency_ms=180)
    print(run.result)  # {"trace_id": ..., "total_cost": ...}
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

from agentforge import semconv

DEFAULT_API_URL = os.environ.get("AGENTFORGE_API_URL", "http://localhost:8000")


class _Span:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload


class TraceRun:
    """A single in-progress agent run. Collects spans, then flushes on exit."""

    def __init__(self, client: "AgentForge", name: str) -> None:
        self._client = client
        self.name = name
        self.spans: list[dict[str, Any]] = []
        self.status = "success"
        self.error: str | None = None
        self.started_at: datetime | None = None
        self.ended_at: datetime | None = None
        self.result: dict[str, Any] | None = None
        self._last_index: int | None = None

    # -- recording ------------------------------------------------------
    def llm(
        self,
        model: str,
        *,
        input_tokens: int = 0,
        output_tokens: int = 0,
        provider: str | None = None,
        prompt: str | None = None,
        completion: str | None = None,
        latency_ms: float = 0.0,
        operation: str = "chat",
        parent_index: int | None = None,
        status: str = "success",
        error: str | None = None,
    ) -> int:
        attributes: dict[str, Any] = {}
        if prompt is not None:
            attributes[semconv.GEN_AI_PROMPT] = prompt
        if completion is not None:
            attributes[semconv.GEN_AI_COMPLETION] = completion
        return self._add(
            {
                "name": f"llm:{model}",
                "kind": semconv.KIND_LLM,
                "provider": provider,
                "model": model,
                "operation": operation,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "latency_ms": latency_ms,
                "status": status,
                "error": error,
                "attributes": attributes or None,
                "parent_index": parent_index,
            }
        )

    def tool(
        self,
        name: str,
        *,
        args: Any = None,
        output: Any = None,
        latency_ms: float = 0.0,
        parent_index: int | None = None,
        status: str = "success",
        error: str | None = None,
    ) -> int:
        return self._add(
            {
                "name": f"tool:{name}",
                "kind": semconv.KIND_TOOL,
                "operation": "execute_tool",
                "latency_ms": latency_ms,
                "status": status,
                "error": error,
                "attributes": {"args": args, "output": output},
                "parent_index": parent_index,
            }
        )

    def _add(self, span: dict[str, Any]) -> int:
        if span.get("parent_index") is None and self._last_index is not None:
            span["parent_index"] = self._last_index
        span["started_at"] = _now_iso()
        self.spans.append(span)
        index = len(self.spans) - 1
        self._last_index = index
        return index

    def fail(self, error: str) -> None:
        self.status = "failed"
        self.error = error

    # -- lifecycle ------------------------------------------------------
    def __enter__(self) -> "TraceRun":
        self.started_at = datetime.now(timezone.utc)
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.ended_at = datetime.now(timezone.utc)
        if exc_type is not None:
            self.fail(f"{exc_type.__name__}: {exc}")
        self.result = self._client._flush(self)
        return False  # never suppress exceptions

    def to_payload(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "agent_name": self._client.agent_name,
            "framework": self._client.framework,
            "model": self._client.model,
            "status": self.status,
            "error": self.error,
            "user_email": self._client.user_email,
            "started_at": _iso(self.started_at),
            "ended_at": _iso(self.ended_at),
            "spans": self.spans,
        }


class AgentForge:
    def __init__(
        self,
        agent_name: str,
        *,
        api_url: str | None = None,
        framework: str | None = None,
        model: str | None = None,
        user_email: str | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.agent_name = agent_name
        self.api_url = (api_url or DEFAULT_API_URL).rstrip("/")
        self.framework = framework
        self.model = model
        self.user_email = user_email
        self.timeout = timeout

    def trace(self, name: str) -> TraceRun:
        return TraceRun(self, name)

    def _flush(self, run: TraceRun) -> dict[str, Any]:
        data = json.dumps(run.to_payload()).encode("utf-8")
        request = urllib.request.Request(
            f"{self.api_url}/v1/traces",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:  # pragma: no cover - network error path
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"AgentForge ingest failed ({exc.code}): {detail}") from exc


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None
