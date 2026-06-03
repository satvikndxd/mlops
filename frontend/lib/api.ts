import type { DashboardSummary, TraceDetail, TraceSummary } from "./types";

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
};
