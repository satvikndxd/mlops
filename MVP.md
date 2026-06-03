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

## Phase 1 — Tracing · Costs · Monitoring · Alerts
- Full tracing: replay, execution graph, retries/failures.
- Cost dashboards: daily / monthly / per-agent / per-user spend.
- Monitoring metrics: latency, token usage, failure rate, tool success, hallucination rate.
- Alerting: alert rules, evaluation, alert events.
- Hardened core: JWT auth, RBAC, audit logging, OpenTelemetry, Prometheus `/metrics`.

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
