import { usd } from "@/lib/format";

export function Breakdown({
  items,
}: {
  items: { key: string; cost: number }[];
}) {
  if (!items.length) {
    return <div className="text-sm text-zinc-500">No data yet.</div>;
  }
  const max = Math.max(...items.map((i) => i.cost), 0.000001);
  return (
    <ul className="space-y-3">
      {items.map((item) => (
        <li key={item.key} className="space-y-1">
          <div className="flex items-center justify-between text-sm">
            <span className="truncate capitalize text-zinc-300">{item.key}</span>
            <span className="ml-2 shrink-0 font-medium text-zinc-100">
              {usd(item.cost)}
            </span>
          </div>
          <div className="h-1.5 w-full rounded bg-zinc-800">
            <div
              className="h-full rounded bg-brand/70"
              style={{ width: `${Math.max((item.cost / max) * 100, 2)}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}
