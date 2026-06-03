"use client";

import { useCallback, useEffect, useState } from "react";
import { ALERT_METRICS, type AlertEvent, type AlertRule } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const SEV_STYLES: Record<string, string> = {
  info: "bg-sky-500/15 text-sky-300",
  warning: "bg-amber-500/15 text-amber-300",
  critical: "bg-red-500/15 text-red-300",
};

export default function AlertsPage() {
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [events, setEvents] = useState<AlertEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({
    name: "High failure rate",
    metric: "failure_rate",
    comparator: "gt",
    threshold: 0.1,
    window_hours: 24,
    severity: "warning",
  });

  const load = useCallback(async () => {
    try {
      const [r, e] = await Promise.all([
        fetch(`${API_URL}/v1/alerts/rules`, { cache: "no-store" }).then((x) => x.json()),
        fetch(`${API_URL}/v1/alerts/events`, { cache: "no-store" }).then((x) => x.json()),
      ]);
      setRules(r);
      setEvents(e);
      setError(null);
    } catch {
      setError(`Could not reach the AgentForge API at ${API_URL}.`);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function createRule(ev: React.FormEvent) {
    ev.preventDefault();
    setBusy(true);
    try {
      await fetch(`${API_URL}/v1/alerts/rules`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...form, threshold: Number(form.threshold), cooldown_minutes: 0 }),
      });
      await load();
    } finally {
      setBusy(false);
    }
  }

  async function evaluate() {
    setBusy(true);
    try {
      await fetch(`${API_URL}/v1/alerts/evaluate`, { method: "POST" });
      await load();
    } finally {
      setBusy(false);
    }
  }

  async function toggle(rule: AlertRule) {
    await fetch(`${API_URL}/v1/alerts/rules/${rule.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled: !rule.enabled }),
    });
    await load();
  }

  async function remove(rule: AlertRule) {
    await fetch(`${API_URL}/v1/alerts/rules/${rule.id}`, { method: "DELETE" });
    await load();
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-900/50 bg-red-950/30 p-6 text-sm text-red-200">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Alerts</h1>
          <p className="text-sm text-zinc-500">
            Trace → Metric → Alert. Rules evaluate against live monitoring metrics.
          </p>
        </div>
        <button
          onClick={evaluate}
          disabled={busy}
          className="rounded-lg bg-brand px-4 py-2 text-sm font-medium text-black hover:bg-brand-dark disabled:opacity-50"
        >
          {busy ? "Evaluating…" : "Evaluate now"}
        </button>
      </header>

      <section className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-5">
        <h2 className="mb-4 text-sm font-medium text-zinc-300">New alert rule</h2>
        <form onSubmit={createRule} className="grid grid-cols-2 gap-3 lg:grid-cols-6">
          <input
            className="col-span-2 rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="Rule name"
          />
          <select
            className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm"
            value={form.metric}
            onChange={(e) => setForm({ ...form, metric: e.target.value })}
          >
            {ALERT_METRICS.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
          <select
            className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm"
            value={form.comparator}
            onChange={(e) => setForm({ ...form, comparator: e.target.value })}
          >
            <option value="gt">&gt;</option>
            <option value="gte">≥</option>
            <option value="lt">&lt;</option>
            <option value="lte">≤</option>
          </select>
          <input
            type="number"
            step="any"
            className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm"
            value={form.threshold}
            onChange={(e) => setForm({ ...form, threshold: Number(e.target.value) })}
            placeholder="Threshold"
          />
          <button
            type="submit"
            disabled={busy}
            className="rounded-lg border border-brand bg-brand/10 px-3 py-2 text-sm text-brand hover:bg-brand/20 disabled:opacity-50"
          >
            Add rule
          </button>
        </form>
      </section>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/40">
          <h2 className="border-b border-zinc-800 px-5 py-4 text-sm font-medium text-zinc-300">
            Rules ({rules.length})
          </h2>
          <ul className="divide-y divide-zinc-800/60">
            {rules.map((r) => (
              <li key={r.id} className="flex items-center justify-between px-5 py-3 text-sm">
                <div>
                  <div className="text-zinc-100">{r.name}</div>
                  <div className="text-xs text-zinc-500">
                    {r.metric} {r.comparator} {r.threshold} · {r.window_hours}h ·{" "}
                    <span className={`rounded px-1 ${SEV_STYLES[r.severity]}`}>{r.severity}</span>
                  </div>
                </div>
                <div className="flex items-center gap-3 text-xs">
                  <button onClick={() => toggle(r)} className="text-zinc-400 hover:text-zinc-100">
                    {r.enabled ? "disable" : "enable"}
                  </button>
                  <button onClick={() => remove(r)} className="text-red-400 hover:text-red-300">
                    delete
                  </button>
                </div>
              </li>
            ))}
            {!rules.length && <li className="px-5 py-6 text-sm text-zinc-500">No rules yet.</li>}
          </ul>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900/40">
          <h2 className="border-b border-zinc-800 px-5 py-4 text-sm font-medium text-zinc-300">
            Fired events ({events.length})
          </h2>
          <ul className="divide-y divide-zinc-800/60">
            {events.map((e) => (
              <li key={e.id} className="px-5 py-3 text-sm">
                <div className="flex items-center gap-2">
                  <span className={`rounded px-1.5 py-0.5 text-[11px] ${SEV_STYLES[e.severity]}`}>
                    {e.severity}
                  </span>
                  <span className="text-xs text-zinc-500">
                    {new Date(e.triggered_at).toLocaleString()}
                  </span>
                </div>
                <div className="mt-1 text-zinc-300">{e.message}</div>
              </li>
            ))}
            {!events.length && (
              <li className="px-5 py-6 text-sm text-zinc-500">
                No events yet — click “Evaluate now”.
              </li>
            )}
          </ul>
        </div>
      </section>
    </div>
  );
}
