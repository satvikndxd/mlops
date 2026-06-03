import Link from "next/link";
import { api } from "@/lib/api";
import { ago, ms, num, usd } from "@/lib/format";
import { StatCard, StatusBadge } from "@/components/StatCard";
import { CostChart } from "@/components/CostChart";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  let data;
  try {
    data = await api.dashboard(8);
  } catch {
    return (
      <ErrorState message={`Could not reach the AgentForge API at ${api.baseUrl}.`} />
    );
  }

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="text-sm text-zinc-500">
          Live overview of agent activity, cost, and reliability.
        </p>
      </header>

      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Total traces" value={num(data.total_traces)} />
        <StatCard label="Total cost" value={usd(data.total_cost)} />
        <StatCard label="Total tokens" value={num(data.total_tokens)} />
        <StatCard
          label="Success rate"
          value={`${(data.success_rate * 100).toFixed(1)}%`}
          hint={`${data.active_agents} active agents · avg ${ms(data.avg_latency_ms)}`}
        />
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-5 lg:col-span-2">
          <h2 className="mb-4 text-sm font-medium text-zinc-300">Daily spend</h2>
          <CostChart data={data.cost_by_day} />
        </div>
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-5">
          <h2 className="mb-4 text-sm font-medium text-zinc-300">Spend by provider</h2>
          <ul className="space-y-3">
            {data.cost_by_provider.map((p) => (
              <li key={p.provider} className="flex items-center justify-between text-sm">
                <span className="capitalize text-zinc-400">{p.provider}</span>
                <span className="font-medium">{usd(p.cost)}</span>
              </li>
            ))}
            {!data.cost_by_provider.length && (
              <li className="text-sm text-zinc-500">No spend yet.</li>
            )}
          </ul>
        </div>
      </section>

      <section className="rounded-xl border border-zinc-800 bg-zinc-900/40">
        <div className="flex items-center justify-between border-b border-zinc-800 px-5 py-4">
          <h2 className="text-sm font-medium text-zinc-300">Recent traces</h2>
          <Link href="/traces" className="text-xs text-brand hover:underline">
            View all →
          </Link>
        </div>
        <table className="w-full text-sm">
          <thead className="text-left text-xs uppercase text-zinc-500">
            <tr>
              <th className="px-5 py-3 font-medium">Trace</th>
              <th className="px-5 py-3 font-medium">Status</th>
              <th className="px-5 py-3 font-medium">Tokens</th>
              <th className="px-5 py-3 font-medium">Cost</th>
              <th className="px-5 py-3 font-medium">Latency</th>
              <th className="px-5 py-3 font-medium">When</th>
            </tr>
          </thead>
          <tbody>
            {data.recent_traces.map((t) => (
              <tr key={t.id} className="border-t border-zinc-800/60 hover:bg-zinc-800/30">
                <td className="px-5 py-3">
                  <Link href={`/traces/${t.id}`} className="text-zinc-100 hover:text-brand">
                    {t.name}
                  </Link>
                </td>
                <td className="px-5 py-3">
                  <StatusBadge status={t.status} />
                </td>
                <td className="px-5 py-3 text-zinc-400">{num(t.total_tokens)}</td>
                <td className="px-5 py-3 text-zinc-400">{usd(t.total_cost)}</td>
                <td className="px-5 py-3 text-zinc-400">{ms(t.latency_ms)}</td>
                <td className="px-5 py-3 text-zinc-500">{ago(t.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-red-900/50 bg-red-950/30 p-6">
      <h1 className="text-lg font-semibold text-red-300">Backend unavailable</h1>
      <p className="mt-2 text-sm text-red-200/80">{message}</p>
      <p className="mt-2 text-xs text-red-200/60">
        Start it with <code>docker compose up</code> or <code>uvicorn app.main:app</code>.
      </p>
    </div>
  );
}
