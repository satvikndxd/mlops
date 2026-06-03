"""Trace ingestion — the heart of the steel thread.

Persists a trace and its spans, prices each LLM span via the static pricing
table, writes cost records, and aggregates run-level totals. Cost calculation
runs inline (no Kafka) so Phase 0 has zero external dependencies beyond Postgres.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.metrics import record_trace_metrics
from app.core.semconv import KIND_LLM, KIND_TOOL
from app.integrations.pricing import compute_cost, infer_provider
from app.models import CostRecord, Span, Trace
from app.repositories.agent_repository import AgentRepository
from app.repositories.cost_repository import CostRepository
from app.repositories.trace_repository import TraceRepository
from app.schemas.trace import TraceIn


class IngestService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.agents = AgentRepository(db)
        self.traces = TraceRepository(db)
        self.costs = CostRepository(db)

    def ingest(self, payload: TraceIn) -> Trace:
        org = self.agents.get_or_create_default_org()
        agent = self.agents.get_or_create_agent(org.id, payload.agent_name, payload.framework)
        version = self.agents.get_or_create_version(agent, payload.agent_version, payload.model)

        user = None
        if payload.user_email:
            user = self.agents.get_or_create_user(org.id, payload.user_email)

        trace = Trace(
            organization_id=org.id,
            agent_id=agent.id,
            agent_version_id=version.id,
            user_id=user.id if user else None,
            name=payload.name,
            status=payload.status,
            error=payload.error,
            started_at=payload.started_at,
            ended_at=payload.ended_at,
        )
        self.traces.add(trace)

        created_spans: list[Span] = []
        total_tokens = 0
        total_cost = 0.0
        total_latency = 0.0
        cost_by_provider: dict[str, float] = {}
        tokens_by_provider: dict[str, tuple[int, int]] = {}
        tool_statuses: list[str] = []

        for span_in in payload.spans:
            provider = infer_provider(span_in.model, span_in.provider)
            span_cost = 0.0
            if span_in.kind == KIND_LLM and (span_in.input_tokens or span_in.output_tokens):
                span_cost = float(
                    compute_cost(
                        provider,
                        span_in.model,
                        span_in.input_tokens,
                        span_in.output_tokens,
                    )
                )

            parent_id = None
            if span_in.parent_index is not None and 0 <= span_in.parent_index < len(created_spans):
                parent_id = created_spans[span_in.parent_index].id

            span = Span(
                trace_id=trace.id,
                parent_span_id=parent_id,
                name=span_in.name,
                kind=span_in.kind,
                status=span_in.status,
                error=span_in.error,
                gen_ai_system=provider if provider != "unknown" else span_in.provider,
                gen_ai_request_model=span_in.model,
                gen_ai_operation=span_in.operation,
                input_tokens=span_in.input_tokens,
                output_tokens=span_in.output_tokens,
                latency_ms=span_in.latency_ms,
                cost=span_cost,
                attributes=span_in.attributes,
                started_at=span_in.started_at,
                ended_at=span_in.ended_at,
            )
            self.traces.add_span(span)
            created_spans.append(span)

            total_tokens += span_in.input_tokens + span_in.output_tokens
            total_cost += span_cost
            total_latency += span_in.latency_ms

            if span_in.kind == KIND_TOOL:
                tool_statuses.append(span_in.status)

            if span_in.kind == KIND_LLM and (span_in.input_tokens or span_in.output_tokens):
                cost_by_provider[provider] = cost_by_provider.get(provider, 0.0) + span_cost
                prev_in, prev_out = tokens_by_provider.get(provider, (0, 0))
                tokens_by_provider[provider] = (
                    prev_in + span_in.input_tokens,
                    prev_out + span_in.output_tokens,
                )

            if span_cost > 0:
                self.costs.add(
                    CostRecord(
                        trace_id=trace.id,
                        organization_id=org.id,
                        provider=provider,
                        model=span_in.model or "unknown",
                        input_tokens=span_in.input_tokens,
                        output_tokens=span_in.output_tokens,
                        cost=span_cost,
                        day=self._day(span_in.started_at or trace.started_at),
                    )
                )

        trace.total_tokens = total_tokens
        trace.total_cost = total_cost
        # Prefer wall-clock latency if timestamps provided, else sum of spans.
        trace.latency_ms = self._wall_clock_ms(payload) or total_latency

        self.db.commit()
        self.db.refresh(trace)

        record_trace_metrics(
            agent=agent.name,
            status=trace.status,
            latency_ms=trace.latency_ms,
            cost_by_provider=cost_by_provider,
            tokens_by_provider=tokens_by_provider,
            tool_statuses=tool_statuses,
        )
        return trace

    @staticmethod
    def _day(value: datetime | None):
        return (value or datetime.now(timezone.utc)).date()

    @staticmethod
    def _wall_clock_ms(payload: TraceIn) -> float:
        if payload.started_at and payload.ended_at:
            delta = payload.ended_at - payload.started_at
            return max(delta.total_seconds() * 1000.0, 0.0)
        return 0.0
