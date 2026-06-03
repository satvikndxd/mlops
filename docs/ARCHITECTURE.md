# AgentForge — Architecture

AgentForge is an AgentOps platform for observability, cost tracking, evaluation, governance,
and incident response of AI agents. This document describes the system design, the
clean-architecture layering, the data model, and the key runtime flows.

The build follows a **steel-thread-first, then phased** strategy (see [`../MVP.md`](../MVP.md)).

---

## 1. System overview

```mermaid
flowchart LR
  subgraph Agents["Instrumented agents"]
    SDK["agentforge SDK\n(LangChain / CrewAI / OpenAI Agents)"]
  end

  subgraph Platform["AgentForge platform"]
    API["FastAPI\napi → services → repositories"]
    OPA["OPA\n(policy engine)"]
    KAFKA["Kafka\n(event bus)"]
    REDIS["Redis\n(cache / pub-sub)"]
    WORKERS["Workers\n(cost · alerts · drift · incidents · policy)"]
    PG[("PostgreSQL")]
    MLF["MLflow\n(registry / experiments)"]
  end

  subgraph Observe["Observability"]
    PROM["Prometheus"]
    GRAF["Grafana"]
  end

  FE["Next.js dashboard"]

  SDK -- "OTLP / gen_ai.* traces" --> API
  SDK -- "policy/evaluate (block?)" --> API
  API --> OPA
  API --> PG
  API -- "events" --> KAFKA
  KAFKA --> WORKERS
  WORKERS --> PG
  API <--> REDIS
  API --> MLF
  API -- "/metrics" --> PROM
  PROM --> GRAF
  FE -- "REST + JWT" --> API
```

## 2. Clean architecture (backend)

```
api/         FastAPI routers — HTTP only, no business logic
  ↓ (dependency injection via Depends)
services/    business logic, orchestration, transactions
  ↓
repositories/ data access (repository pattern over SQLAlchemy)
  ↓
models/      SQLAlchemy ORM entities
schemas/     Pydantic request/response models (the API contract)
core/        config, db, security (JWT/RBAC), logging, otel, semconv
events/      Kafka producer + event types
integrations/ pricing tables, mlflow, evidently
```

Rules: routers never touch the ORM directly; services depend on repository interfaces;
repositories are the only layer that builds SQL. This keeps domains testable and swappable.

## 3. Event-driven flow

Trace ingestion is synchronous for persistence (so the client gets an id) and **asynchronous**
for derived work. The API publishes domain events to Kafka; workers consume them:

| Event | Consumer | Phase |
|-------|----------|-------|
| `trace.ingested` | cost aggregation | 1 |
| `metric.window.closed` | alert evaluation | 1 |
| `span.received` | policy evaluation | 2 |
| `alert.fired` / `policy.violation` | incident detection | 2 |
| `trace.sampled` | drift sampling | 4 |

In Phase 0 the cost calculation runs inline in the ingest service (no Kafka dependency) so the
steel thread has zero external moving parts beyond Postgres; Kafka is introduced in Phase 1.

## 4. Data model (ER)

```mermaid
erDiagram
  ORGANIZATION ||--o{ USER : has
  ORGANIZATION ||--o{ AGENT : owns
  AGENT ||--o{ AGENT_VERSION : has
  AGENT ||--o{ TRACE : runs
  AGENT_VERSION ||--o{ TRACE : produces
  TRACE ||--o{ SPAN : contains
  TRACE ||--o{ COST_RECORD : incurs
  USER ||--o{ TRACE : initiates

  ORGANIZATION {
    uuid id PK
    string name
    string slug
  }
  USER {
    uuid id PK
    uuid organization_id FK
    string email
    string hashed_password
    string role
  }
  AGENT {
    uuid id PK
    uuid organization_id FK
    string name
    string framework
  }
  AGENT_VERSION {
    uuid id PK
    uuid agent_id FK
    int version
    string model
    text prompt
    json tools
    string status
  }
  TRACE {
    uuid id PK
    uuid organization_id FK
    uuid agent_id FK
    uuid agent_version_id FK
    uuid user_id FK
    string name
    string status
    float latency_ms
    int total_tokens
    numeric total_cost
    datetime started_at
    datetime ended_at
  }
  SPAN {
    uuid id PK
    uuid trace_id FK
    uuid parent_span_id FK
    string name
    string kind
    string gen_ai_system
    string gen_ai_request_model
    int input_tokens
    int output_tokens
    float latency_ms
    string status
    json attributes
  }
  COST_RECORD {
    uuid id PK
    uuid trace_id FK
    uuid organization_id FK
    string provider
    string model
    int input_tokens
    int output_tokens
    numeric cost
    date day
  }
```

> Phase 1+ adds: `ApiKey`, `AlertRule`/`Alert`/`AlertEvent`, `AuditLog`. Phase 2+ adds:
> `Policy`/`PolicyDecision`/`PolicyViolation`, `Incident`/`IncidentEvent`/`RootCauseAnalysis`/
> `RemediationSuggestion`/`Postmortem`. Phase 3+ adds `MCPServer`/`MCPTool`/`MCPCapability`,
> `EvaluationRun`/`EvaluationResult`, `Deployment`. Phase 4 adds `Experiment*`, `DriftReport`.

## 5. Key sequence — trace ingestion (Phase 0)

```mermaid
sequenceDiagram
  participant A as Agent (SDK)
  participant API as FastAPI /v1/traces
  participant S as IngestService
  participant P as PricingTable
  participant DB as Postgres

  A->>API: POST /v1/traces {trace, spans[]}
  API->>S: ingest(payload)
  S->>DB: INSERT trace + spans
  loop each LLM span
    S->>P: price(provider, model, in_tok, out_tok)
    P-->>S: cost
    S->>DB: INSERT cost_record
  end
  S->>DB: UPDATE trace.total_cost / total_tokens / latency
  S-->>API: trace_id
  API-->>A: 201 {trace_id, total_cost}
```

## 6. Key sequence — policy enforcement (Phase 2)

```mermaid
sequenceDiagram
  participant A as Agent (SDK @enforce)
  participant API as /v1/policy/evaluate
  participant OPA as OPA (Rego)
  participant DB as Postgres
  A->>API: evaluate(action context)
  API->>OPA: POST /v1/data/agentforge/decision
  OPA-->>API: {allow|deny, rule}
  alt deny (block mode)
    API->>DB: PolicyDecision + PolicyViolation
    API-->>A: 403 deny → SDK raises, tool call blocked
    API->>DB: open Incident (if high severity)
  else allow
    API-->>A: 200 allow
  end
```

## 7. Key sequence — incident response (Phase 2)

```mermaid
sequenceDiagram
  participant W as Worker (detector)
  participant DB as Postgres
  participant RCA as RCA engine
  W->>DB: read traces/spans/alerts/violations
  W->>DB: create Incident + timeline
  W->>RCA: analyze(incident)
  RCA->>DB: read evidence spans + registry diff
  RCA-->>W: ranked causes + remediation
  W->>DB: persist RootCauseAnalysis + RemediationSuggestion
  W->>DB: render Postmortem (markdown + json)
```

## 8. Observability

- The SDK emits OpenTelemetry spans using **GenAI semantic conventions**
  (`gen_ai.system`, `gen_ai.request.model`, `gen_ai.usage.input_tokens`/`output_tokens`,
  `gen_ai.operation.name`, plus `gen_ai.agent.name` / `gen_ai.tool.name`). `core/semconv.py`
  is the single source of truth for these keys.
- The backend is itself instrumented with OpenTelemetry and exposes Prometheus metrics at
  `/metrics`. Grafana provisions dashboards for latency, cost, failure rate, and tokens.

## 9. Deployment topology

- **Local / demo**: `docker compose` (Postgres, Redis, Kafka, MLflow, OPA, Prometheus,
  Grafana, backend, worker, frontend).
- **Production**: Kubernetes via Helm chart; each service a Deployment + Service, ingress for
  API + frontend, secrets for DB/JWT, HPA on the API and workers. Cloud-ready for AWS/GCP
  (managed Postgres, managed Kafka, object storage for MLflow artifacts).
