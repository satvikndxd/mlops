"""Runnable example: a simple multi-step agent emitting a trace to AgentForge.

Usage:
    export AGENTFORGE_API_URL=http://localhost:8000
    python sdk/examples/simple_agent.py
"""

from __future__ import annotations

import time

from agentforge import AgentForge


def run() -> None:
    af = AgentForge(
        agent_name="research-agent",
        framework="langchain",
        model="gpt-4o-mini",
        user_email="demo@agentforge.dev",
    )

    with af.trace("answer_question") as agent_run:
        # Step 1: plan with an LLM call.
        t0 = time.perf_counter()
        time.sleep(0.05)  # simulate latency
        agent_run.llm(
            "gpt-4o-mini",
            input_tokens=850,
            output_tokens=120,
            provider="openai",
            prompt="User asks: what is AgentOps? Decide which tools to use.",
            completion="Plan: search the web, then summarize.",
            latency_ms=(time.perf_counter() - t0) * 1000,
        )

        # Step 2: call a tool.
        t0 = time.perf_counter()
        time.sleep(0.03)
        agent_run.tool(
            "web_search",
            args={"q": "AgentOps observability for AI agents"},
            output={"results": 5},
            latency_ms=(time.perf_counter() - t0) * 1000,
        )

        # Step 3: synthesize the final answer with another LLM call.
        t0 = time.perf_counter()
        time.sleep(0.04)
        agent_run.llm(
            "gpt-4o-mini",
            input_tokens=1400,
            output_tokens=380,
            provider="openai",
            prompt="Summarize the search results into an answer.",
            completion="AgentOps is the practice of operating AI agents in production…",
            latency_ms=(time.perf_counter() - t0) * 1000,
        )

    print("Trace ingested:")
    for key, value in (agent_run.result or {}).items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    run()
