export interface TraceSummary {
  id: string;
  name: string;
  agent_id: string;
  status: string;
  latency_ms: number;
  total_tokens: number;
  total_cost: number;
  started_at: string | null;
  ended_at: string | null;
  created_at: string;
}

export interface Span {
  id: string;
  parent_span_id: string | null;
  name: string;
  kind: string;
  status: string;
  error: string | null;
  gen_ai_system: string | null;
  gen_ai_request_model: string | null;
  gen_ai_operation: string | null;
  input_tokens: number;
  output_tokens: number;
  latency_ms: number;
  cost: number;
  attributes: Record<string, unknown> | null;
  started_at: string | null;
  ended_at: string | null;
}

export interface TraceDetail extends TraceSummary {
  error: string | null;
  spans: Span[];
}

export interface DayCost {
  day: string;
  cost: number;
}

export interface ProviderCost {
  provider: string;
  cost: number;
}

export interface DashboardSummary {
  total_traces: number;
  total_cost: number;
  total_tokens: number;
  avg_latency_ms: number;
  success_rate: number;
  active_agents: number;
  cost_by_day: DayCost[];
  cost_by_provider: ProviderCost[];
  recent_traces: TraceSummary[];
}

export interface Agent {
  id: string;
  name: string;
  framework: string | null;
  description: string | null;
}
