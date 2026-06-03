import type { MetricPoint } from "@/lib/types";

export function SeriesChart({
  points,
  format,
  color = "bg-sky-500/70",
}: {
  points: MetricPoint[];
  format: (v: number) => string;
  color?: string;
}) {
  if (!points.length) {
    return <div className="text-sm text-zinc-500">No data in this window.</div>;
  }
  const max = Math.max(...points.map((p) => p.value), 0.000001);
  return (
    <div className="flex h-40 items-end gap-1">
      {points.map((p) => (
        <div
          key={p.bucket}
          className="group flex flex-1 flex-col items-center justify-end"
          title={`${new Date(p.bucket).toLocaleDateString()}: ${format(p.value)}`}
        >
          <div
            className={`w-full rounded-t ${color} transition group-hover:opacity-100 opacity-80`}
            style={{ height: `${Math.max((p.value / max) * 100, 2)}%` }}
          />
        </div>
      ))}
    </div>
  );
}
