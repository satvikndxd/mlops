import { api } from "@/lib/api";
import { ms, num } from "@/lib/format";
import { StatCard } from "@/components/StatCard";
import { SeriesChart } from "@/components/SeriesChart";

export const dynamic = "force-dynamic";

export default async function MonitoringPage() {
  let overview, volume, latency, failure;
  try {
    [overview, volume, latency, failure] = await Promise.all([
      api.monitoringOverview(720),
      api.monitoringTimeseries("volume", 720, "day"),
      api.monitoringTimeseries("latency_p95", 720, "day"),
      api.monitoringTimeseries("failure_rate", 720, "day"),
    ]);
  } catch {
    return (
      <div className="rounded-xl border border-red-900/50 bg-red-950/30 p-6 text-sm text-red-200">
        Could not reach the AgentForge API at {api.baseUrl}.
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-semibold">Monitoring</h1>
        <p className="text-sm text-zinc-500">
          Last {Math.round(overview.window_hours / 24)} days · {num(overview.total_traces)} runs.
        </p>
      </header>

      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard
          label="Success rate"
          value={`${(overview.success_rate * 100).toFixed(1)}%`}
          hint={`${(overview.failure_rate * 100).toFixed(1)}% failures`}
        />
        <StatCard label="p95 latency" value={ms(overview.p95_latency_ms)} hint={`p50 ${ms(overview.p50_latency_ms)}`} />
        <StatCard
          label="Tool success"
          value={`${(overview.tool_success_rate * 100).toFixed(1)}%`}
        />
        <StatCard
          label="Throughput"
          value={`${overview.throughput_per_hour.toFixed(2)}/h`}
          hint={`${num(overview.total_tokens)} tokens`}
        />
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <ChartCard title="Run volume (daily)">
          <SeriesChart points={volume.points} format={(v) => `${v} runs`} color="bg-emerald-500/70" />
        </ChartCard>
        <ChartCard title="p95 latency (daily)">
          <SeriesChart points={latency.points} format={ms} color="bg-sky-500/70" />
        </ChartCard>
        <ChartCard title="Failure rate (daily)">
          <SeriesChart
            points={failure.points}
            format={(v) => `${(v * 100).toFixed(1)}%`}
            color="bg-red-500/70"
          />
        </ChartCard>
      </section>

      <p className="text-xs text-zinc-600">
        Hallucination rate is reported once Evaluation (Phase 3) writes eval results;
        currently {overview.hallucination_rate === null ? "not measured" : `${overview.hallucination_rate}`}.
      </p>
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-5">
      <h2 className="mb-4 text-sm font-medium text-zinc-300">{title}</h2>
      {children}
    </div>
  );
}
