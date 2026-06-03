import { api } from "@/lib/api";
import type { Agent } from "@/lib/types";

export const dynamic = "force-dynamic";

async function getAgents(): Promise<Agent[]> {
  const res = await fetch(`${api.baseUrl}/v1/agents`, { cache: "no-store" });
  if (!res.ok) throw new Error("failed");
  return res.json();
}

export default async function AgentsPage() {
  let agents: Agent[];
  try {
    agents = await getAgents();
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
        <h1 className="text-2xl font-semibold">Agents</h1>
        <p className="text-sm text-zinc-500">{agents.length} registered agents.</p>
      </header>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {agents.map((a) => (
          <div
            key={a.id}
            className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-5"
          >
            <div className="flex items-center justify-between">
              <h2 className="font-medium text-zinc-100">{a.name}</h2>
              {a.framework && (
                <span className="rounded bg-zinc-800 px-2 py-0.5 text-[11px] text-zinc-400">
                  {a.framework}
                </span>
              )}
            </div>
            <p className="mt-2 text-sm text-zinc-500">
              {a.description ?? "No description."}
            </p>
          </div>
        ))}
        {!agents.length && (
          <div className="text-sm text-zinc-500">No agents yet.</div>
        )}
      </div>
    </div>
  );
}
