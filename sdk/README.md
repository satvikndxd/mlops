# AgentForge SDK

Trace AI agents to an [AgentForge](../README.md) backend using OpenTelemetry GenAI
semantic conventions. Zero hard dependencies.

```bash
pip install -e .
```

```python
from agentforge import AgentForge

af = AgentForge(agent_name="research-agent", framework="langchain")
with af.trace("answer_question") as run:
    run.llm("gpt-4o-mini", input_tokens=1200, output_tokens=320,
            provider="openai", prompt="...", completion="...", latency_ms=420)
    run.tool("web_search", args={"q": "agentops"}, output={"hits": 5}, latency_ms=180)

print(run.result)  # {"trace_id": "...", "total_cost": 0.00037, ...}
```

CLI:

```bash
export AGENTFORGE_API_URL=http://localhost:8000
agentforge ping     # health check
agentforge demo     # emit a sample trace
```
