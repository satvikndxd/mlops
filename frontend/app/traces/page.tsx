import Link from "next/link";
import { api } from "@/lib/api";
import { ago, ms, num, usd } from "@/lib/format";
import { StatusBadge } from "@/components/StatCard";

export const dynamic = "force-dynamic";

export default async function TracesPage() {
  let traces;
  try {
    traces = await api.traces(200);
  } catch {
    return (
      <div className="rounded-xl border border-red-900/50 bg-red-950/30 p-6 text-sm text-red-200">
        Could not reach the AgentForge API at {api.baseUrl}.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Traces</h1>
        <p className="text-sm text-zinc-500">{traces.length} runs · click a trace to replay.</p>
      </header>

      <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900/40">
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
            {traces.map((t) => (
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
            {!traces.length && (
              <tr>
                <td colSpan={6} className="px-5 py-8 text-center text-zinc-500">
                  No traces yet — run the SDK example to emit one.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
