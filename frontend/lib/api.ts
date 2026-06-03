import type {
  CostBreakdownItem,
  CostSummary,
  DashboardSummary,
  DayCost,
  MonitoringOverview,
  MonthCost,
  TimeSeries,
  TraceDetail,
  TraceSummary,
} from "./types";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`API ${path} failed: ${res.status}`);
  }
  return (await res.json()) as T;
}

export const api = {
  baseUrl: API_URL,
  dashboard: (limit = 10) =>
    get<DashboardSummary>(`/v1/dashboard/summary?recent_limit=${limit}`),
  traces: (limit = 100) => get<TraceSummary[]>(`/v1/traces?limit=${limit}`),
  trace: (id: string) => get<TraceDetail>(`/v1/traces/${id}`),

  monitoringOverview: (windowHours = 720) =>
    get<MonitoringOverview>(`/v1/monitoring/overview?window_hours=${windowHours}`),
  monitoringTimeseries: (metric: string, hours = 720, bucket = "day") =>
    get<TimeSeries>(
      `/v1/monitoring/timeseries?metric=${metric}&hours=${hours}&bucket=${bucket}`,
    ),

  costSummary: () => get<CostSummary>(`/v1/costs/summary`),
  costBy: (dim: "provider" | "model" | "agent" | "user") =>
    get<CostBreakdownItem[]>(`/v1/costs/by-${dim}`),
  costDaily: () => get<DayCost[]>(`/v1/costs/daily`),
  costMonthly: () => get<MonthCost[]>(`/v1/costs/monthly`),
};
