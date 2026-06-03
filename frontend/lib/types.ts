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

export interface MonitoringOverview {
  window_hours: number;
  total_traces: number;
  throughput_per_hour: number;
  success_rate: number;
  failure_rate: number;
  avg_latency_ms: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  total_tokens: number;
  total_cost: number;
  tool_success_rate: number;
  hallucination_rate: number | null;
}

export interface MetricPoint {
  bucket: string;
  value: number;
}

export interface TimeSeries {
  metric: string;
  bucket: string;
  points: MetricPoint[];
}

export interface CostSummary {
  today: number;
  this_month: number;
  all_time: number;
  currency: string;
}

export interface CostBreakdownItem {
  key: string;
  cost: number;
}

export interface MonthCost {
  month: string;
  cost: number;
}

export interface AlertRule {
  id: string;
  name: string;
  metric: string;
  comparator: string;
  threshold: number;
  window_hours: number;
  severity: string;
  channel: string;
  enabled: boolean;
  cooldown_minutes: number;
  last_triggered_at: string | null;
}

export interface AlertEvent {
  id: string;
  rule_id: string;
  triggered_at: string;
  metric: string;
  metric_value: number;
  threshold: number;
  severity: string;
  status: string;
  message: string;
}

export const ALERT_METRICS = [
  "failure_rate",
  "success_rate",
  "avg_latency_ms",
  "p95_latency_ms",
  "tool_success_rate",
  "throughput_per_hour",
  "total_cost",
] as const;
