# AgentForge — MVP & Scope Contract

This file is the **binding scope contract** for AgentForge. It exists to keep the build
disciplined: we ship a working **steel thread** first, then expand strictly one phase at a
time. **No phase is started until the previous phase works end-to-end and is committed.**

> Golden rule: never be "half-built everywhere." Be fully-built somewhere, then grow.

---

## Phase 0 — STEEL THREAD  ✅ first priority

The thinnest possible end-to-end slice that proves the whole architecture:

```
Python SDK  →  FastAPI ingest  →  Postgres (Trace + Span)  →  Cost calculation  →  Dashboard
```

**One trace. One agent. One dashboard. End-to-end.**

Success criteria:
- The SDK example agent emits a trace over HTTP.
- The backend persists `Trace` + `Span` rows (OpenTelemetry `gen_ai.*` attributes).
- A `CostRecord` is computed from token usage using the static pricing table.
- The dashboard shows recent traces and total cost.

When this works, the foundation that every other feature depends on is proven.

---

## Phase 1 — Observability loop, then auth (reordered by review)

Build the engineering-hard observability loop first; auth last. Introduce **Redis now**
(caching / rate limiting / live updates) and **defer Kafka to Phase 2**, where the Policy
Engine and Incident Response actually need event streams. (At 10s–1000s of traces, Kafka
solves a scale problem we don't have yet; Redis solves problems we have now.)

- **Phase 1A — Prometheus metrics · Monitoring · Cost analytics** ✅ builds directly on the
  trace pipeline: `/metrics` endpoint + domain metrics; monitoring overview + time-series
  (latency p50/p95, throughput, failure rate, tool-success rate, tokens, cost); cost
  analytics (today / month / all-time, by agent / provider / model / user, daily / monthly).
- **Phase 1B — Alert rules · Alert events**: completes the loop **Trace → Metric → Alert**.
- **Phase 1C — JWT · RBAC · Audit logging**: secure the API once the value is proven.
- **Redis** (after 1C): response caching, rate limiting, live dashboard updates.
- Full tracing polish: replay, execution graph, retries/failures (already in steel thread).

> Kafka moves to the **start of Phase 2**, introduced alongside the Policy Engine / Incident
> Response event streams — not before.

## Phase 2 — Policy Engine · Incident Response
- Policy Engine (OPA / Rego): `max_cost_per_run`, `max_tokens_per_run`,
  `prohibit_shell_exec`, `no_tool_call_after_prompt_injection`; monitor & block modes.
- Incident Response: detection → timeline → root-cause analysis → remediation → postmortem.

## Phase 3 — MCP Registry · Evaluation · Agent Registry
- MCP Registry: server registry, tool registry, capability discovery.
- Evaluation: pipelines, metrics, benchmark runs, Evaluation-as-Code (`evaluations/*.yaml`).
- Agent Registry: versions, prompts, tools, deployments, rollback (MLflow-backed).

## Phase 4 — Experiments · Drift Detection
- Experiments: prompt / model / tool experiments + A/B testing.
- Drift Detection: Evidently reports over prompts / responses / user behavior.

## Phase 5 — AgentSight (eBPF)  ⟶  v2 / optional stretch
- Kernel-level process/syscall observation correlated with LLM + tool calls.
- Infinite-loop and prompt-injection detection. Deliberately last — eBPF is a rabbit hole and
  the platform is complete and demoable without it.

---

## Out of scope until their phase
Incident Response, MCP Registry, Drift, Experiments, Evaluation, Policy Engine, AgentSight are
**explicitly not built** until their phase above. This is intentional.

## Demo driver
Scenario benchmarks (`benchmarks/*.yaml`) + `agentforge benchmark run <scenario>` exercise the
full chain once Phase 2 lands (e.g. `policy_violation`:
Violation Detected → Policy Blocked → Incident Created → RCA Generated → Postmortem Exported).
