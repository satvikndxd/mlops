import { api } from "@/lib/api";
import { usd } from "@/lib/format";
import { StatCard } from "@/components/StatCard";
import { CostChart } from "@/components/CostChart";
import { Breakdown } from "@/components/Breakdown";

export const dynamic = "force-dynamic";

export default async function CostsPage() {
  let summary, daily, byProvider, byModel, byAgent;
  try {
    [summary, daily, byProvider, byModel, byAgent] = await Promise.all([
      api.costSummary(),
      api.costDaily(),
      api.costBy("provider"),
      api.costBy("model"),
      api.costBy("agent"),
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
        <h1 className="text-2xl font-semibold">Costs</h1>
        <p className="text-sm text-zinc-500">
          Spend across OpenAI, Anthropic, Gemini, and DeepSeek.
        </p>
      </header>

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard label="Today" value={usd(summary.today)} />
        <StatCard label="This month" value={usd(summary.this_month)} />
        <StatCard label="All time" value={usd(summary.all_time)} />
      </section>

      <section className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-5">
        <h2 className="mb-4 text-sm font-medium text-zinc-300">Daily spend</h2>
        <CostChart data={daily} />
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <BreakdownCard title="By provider" items={byProvider} />
        <BreakdownCard title="By model" items={byModel} />
        <BreakdownCard title="By agent" items={byAgent} />
      </section>
    </div>
  );
}

function BreakdownCard({
  title,
  items,
}: {
  title: string;
  items: { key: string; cost: number }[];
}) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-5">
      <h2 className="mb-4 text-sm font-medium text-zinc-300">{title}</h2>
      <Breakdown items={items} />
    </div>
  );
}
