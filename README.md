<div align="center">

# 🔥 AgentForge

**Open-source AgentOps platform — observability, cost tracking, evaluation, governance, and incident response for AI agents.**

An open alternative to AgentOps / LangSmith and parts of MLflow, focused on AI agents.

</div>

---

## Why AgentForge

Modern AI agents are non-deterministic, multi-step, tool-using, and expensive. AgentForge gives
you the full operational loop for them:

> **Observe → Detect → Enforce → Resolve**

- **Trace** every prompt, response, tool call, retry, and failure (OpenTelemetry `gen_ai.*` semantic conventions).
- **Track cost** across OpenAI, Anthropic, Gemini, and DeepSeek.
- **Monitor** latency, token usage, failure rate, tool success, and hallucination rate, with alerting.
- **Evaluate** agents with pipelines, benchmarks, and Evaluation-as-Code (CI deploy gate).
- **Govern** agents with a Policy Engine (OPA / Rego) that can *block* unsafe actions.
- **Respond** to incidents with automated detection → timeline → root-cause → remediation → postmortem.
- **Register** agent versions, prompts, tools, deployments (with rollback) and discover MCP tools.

## Tech stack

| Area | Tech |
|------|------|
| Backend | Python · FastAPI · SQLAlchemy · Alembic · PostgreSQL |
| AI infra | MLflow · OpenTelemetry · LangChain · CrewAI · OpenAI Agents SDK |
| Streaming / cache | Kafka · Redis |
| Monitoring | Prometheus · Grafana · Evidently |
| Governance | Open Policy Agent (Rego) |
| Auth | JWT · RBAC |
| Frontend | Next.js · TypeScript · TailwindCSS · shadcn/ui |
| Deploy | Docker · Docker Compose · Kubernetes · Helm |
| CI/CD | GitHub Actions |

## Repository layout

```
backend/         FastAPI app (clean architecture: api → services → repositories → models)
sdk/             agentforge Python SDK (tracer, decorators, OTel exporter, CLI)
frontend/        Next.js + TS + Tailwind + shadcn/ui dashboard
evaluations/     Evaluation-as-Code YAML suites + runner
benchmarks/      Scenario benchmarks (self-demonstrating end-to-end chains)
policies/        OPA / Rego governance rules
infrastructure/  docker-compose + env templates
deployments/     Kubernetes manifests + Helm chart
monitoring/      Prometheus + Grafana configs
agentsight/      eBPF agent monitoring (v2 / optional stretch)
docs/            Architecture, ER, sequence diagrams, guides, API docs
```

## Quickstart (steel thread)

```bash
# 1. Bring up Postgres + backend + frontend
cd infrastructure && docker compose up -d --build

# 2. Run database migrations + seed
docker compose exec backend alembic upgrade head
docker compose exec backend python -m seeds.seed

# 3. Emit a trace with the SDK example
pip install -e sdk
AGENTFORGE_API_URL=http://localhost:8000 python sdk/examples/simple_agent.py

# 4. Open the dashboard
open http://localhost:3000
```

Backend API docs: <http://localhost:8000/docs> · Health: <http://localhost:8000/healthz>

## Project status

Built **steel-thread-first**, then expanded by phase — see [`MVP.md`](./MVP.md) for the scope
contract and [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) for the design.

- ✅ **Phase 0 — Steel thread**: SDK → ingest → Postgres → cost calc → dashboard
- ⏳ Phase 1: Tracing · Costs · Monitoring · Alerts
- ⏳ Phase 2: Policy Engine · Incident Response
- ⏳ Phase 3: MCP Registry · Evaluation · Agent Registry
- ⏳ Phase 4: Experiments · Drift Detection
- 🔭 Phase 5: AgentSight (eBPF) — v2

## License

MIT
