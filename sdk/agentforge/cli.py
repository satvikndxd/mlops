"""AgentForge command-line interface.

    agentforge ping              # check backend health
    agentforge demo              # emit a sample trace end-to-end

(The ``benchmark`` subcommand for scenario chains arrives in Phase 2.)
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request

from agentforge.client import DEFAULT_API_URL, AgentForge


def _ping(api_url: str) -> int:
    try:
        with urllib.request.urlopen(f"{api_url}/healthz", timeout=5) as resp:
            body = json.loads(resp.read().decode())
        print(f"OK  {api_url} -> {body}")
        return 0
    except Exception as exc:  # pragma: no cover - network error path
        print(f"FAIL {api_url}: {exc}", file=sys.stderr)
        return 1


def _demo(api_url: str) -> int:
    af = AgentForge(agent_name="demo-agent", framework="langchain", api_url=api_url)
    with af.trace("cli_demo") as run:
        run.llm("gpt-4o-mini", input_tokens=900, output_tokens=240, provider="openai",
                prompt="What is AgentOps?", completion="Operations for AI agents.",
                latency_ms=350.0)
        run.tool("web_search", args={"q": "AgentOps"}, output={"hits": 3}, latency_ms=120.0)
    print(json.dumps(run.result, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agentforge", description="AgentForge CLI")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="AgentForge backend URL")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("ping", help="check backend health")
    sub.add_parser("demo", help="emit a sample trace")

    args = parser.parse_args(argv)
    if args.command == "ping":
        return _ping(args.api_url)
    if args.command == "demo":
        return _demo(args.api_url)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
