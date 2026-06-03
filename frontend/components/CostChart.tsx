import type { DayCost } from "@/lib/types";
import { usd } from "@/lib/format";

export function CostChart({ data }: { data: DayCost[] }) {
  if (!data.length) {
    return <div className="text-sm text-zinc-500">No cost data yet.</div>;
  }
  const max = Math.max(...data.map((d) => d.cost), 0.000001);
  return (
    <div className="flex h-40 items-end gap-1">
      {data.map((d) => (
        <div key={d.day} className="group flex flex-1 flex-col items-center justify-end">
          <div
            className="w-full rounded-t bg-brand/70 transition group-hover:bg-brand"
            style={{ height: `${Math.max((d.cost / max) * 100, 2)}%` }}
            title={`${d.day}: ${usd(d.cost)}`}
          />
        </div>
      ))}
    </div>
  );
}
