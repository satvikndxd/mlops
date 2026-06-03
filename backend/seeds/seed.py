"""Seed the database with a demo organization, user, and sample traces.

Run after migrations:  ``python -m seeds.seed``
Reuses the real ingest path so seeded data is identical in shape to live data.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from app.core.database import SessionLocal
from app.core.logging import configure_logging, get_logger
from app.models import User
from app.repositories.agent_repository import AgentRepository
from app.schemas.trace import SpanIn, TraceIn
from app.services.ingest_service import IngestService

logger = get_logger("seed")

# Deterministic-ish sample matrix of (agent, framework, model, provider).
AGENTS = [
    ("research-agent", "langchain", "gpt-4o-mini", "openai"),
    ("support-bot", "crewai", "claude-3-5-sonnet", "anthropic"),
    ("data-analyst", "openai-agents", "gemini-1.5-flash", "gemini"),
]

TASKS = ["answer_question", "summarize_docs", "plan_steps", "extract_entities", "draft_reply"]
TOOLS = ["web_search", "vector_lookup", "calculator", "sql_query"]


def _make_trace(rng: random.Random, idx: int) -> TraceIn:
    agent_name, framework, model, provider = rng.choice(AGENTS)
    n_steps = rng.randint(2, 4)
    started = datetime.now(timezone.utc) - timedelta(days=rng.randint(0, 13), minutes=rng.randint(0, 600))
    spans: list[SpanIn] = []

    cursor = started
    for step in range(n_steps):
        latency = rng.uniform(180, 1400)
        if step % 2 == 0:
            spans.append(
                SpanIn(
                    name=f"llm:{model}",
                    kind="llm",
                    provider=provider,
                    model=model,
                    operation="chat",
                    input_tokens=rng.randint(200, 1800),
                    output_tokens=rng.randint(60, 700),
                    latency_ms=latency,
                    attributes={"gen_ai.prompt": "…", "gen_ai.completion": "…"},
                    started_at=cursor,
                    ended_at=cursor + timedelta(milliseconds=latency),
                )
            )
        else:
            spans.append(
                SpanIn(
                    name=f"tool:{rng.choice(TOOLS)}",
                    kind="tool",
                    operation="execute_tool",
                    latency_ms=latency,
                    status="success" if rng.random() > 0.1 else "error",
                    attributes={"args": {"q": "demo"}},
                    started_at=cursor,
                    ended_at=cursor + timedelta(milliseconds=latency),
                    parent_index=max(step - 1, 0),
                )
            )
        cursor += timedelta(milliseconds=latency)

    status = "success" if rng.random() > 0.12 else "failed"
    return TraceIn(
        name=f"{rng.choice(TASKS)}#{idx}",
        agent_name=agent_name,
        framework=framework,
        model=model,
        status=status,
        error=None if status == "success" else "tool timeout after 3 retries",
        user_email="demo@agentforge.dev",
        started_at=started,
        ended_at=cursor,
        spans=spans,
    )


def main(n_traces: int = 40, seed: int = 7) -> None:
    configure_logging("INFO")
    rng = random.Random(seed)
    db = SessionLocal()
    try:
        repo = AgentRepository(db)
        org = repo.get_or_create_default_org()

        if repo.get_user_by_email("demo@agentforge.dev") is None:
            db.add(
                User(
                    organization_id=org.id,
                    email="demo@agentforge.dev",
                    full_name="Demo Admin",
                    role="owner",
                )
            )
            db.commit()

        ingest = IngestService(db)
        for idx in range(n_traces):
            ingest.ingest(_make_trace(rng, idx))

        logger.info("Seeded %d traces for org '%s'", n_traces, org.slug)
    finally:
        db.close()


if __name__ == "__main__":
    main()
