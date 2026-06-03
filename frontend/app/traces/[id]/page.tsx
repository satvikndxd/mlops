import Link from "next/link";
import { api } from "@/lib/api";
import { ms, num, usd } from "@/lib/format";
import { StatCard, StatusBadge } from "@/components/StatCard";
import type { Span } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function TraceDetailPage({
  params,
}: {
  params: { id: string };
}) {
  let trace;
  try {
    trace = await api.trace(params.id);
  } catch {
    return (
      <div className="rounded-xl border border-red-900/50 bg-red-950/30 p-6 text-sm text-red-200">
        Trace not found or API unavailable.
        <div className="mt-3">
          <Link href="/traces" className="text-brand hover:underline">
            ← Back to traces
          </Link>
        </div>
      </div>
    );
  }

  const maxLatency = Math.max(...trace.spans.map((s) => s.latency_ms), 1);

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <Link href="/traces" className="text-xs text-brand hover:underline">
          ← Back to traces
        </Link>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold">{trace.name}</h1>
          <StatusBadge status={trace.status} />
        </div>
        <p className="font-mono text-xs text-zinc-500">{trace.id}</p>
        {trace.error && (
          <p className="rounded-lg bg-red-950/40 px-3 py-2 text-sm text-red-300">
            {trace.error}
          </p>
        )}
      </header>

      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Spans" value={num(trace.spans.length)} />
        <StatCard label="Tokens" value={num(trace.total_tokens)} />
        <StatCard label="Cost" value={usd(trace.total_cost)} />
        <StatCard label="Latency" value={ms(trace.latency_ms)} />
      </section>

      <section className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-5">
        <h2 className="mb-4 text-sm font-medium text-zinc-300">
          Execution graph &amp; replay
        </h2>
        <ol className="space-y-2">
          {trace.spans.map((s, i) => (
            <SpanRow key={s.id} span={s} index={i} maxLatency={maxLatency} />
          ))}
        </ol>
      </section>
    </div>
  );
}

function SpanRow({
  span,
  index,
  maxLatency,
}: {
  span: Span;
  index: number;
  maxLatency: number;
}) {
  const indent = span.parent_span_id ? 24 : 0;
  const color =
    span.kind === "llm"
      ? "bg-sky-500/70"
      : span.kind === "tool"
        ? "bg-violet-500/70"
        : "bg-zinc-500/70";
  return (
    <li
      className="rounded-lg border border-zinc-800/70 bg-zinc-950/40 p-3"
      style={{ marginLeft: indent }}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-zinc-600">#{index}</span>
          <span
            className={`rounded px-1.5 py-0.5 text-[10px] uppercase ${
              span.kind === "llm"
                ? "bg-sky-500/15 text-sky-300"
                : "bg-violet-500/15 text-violet-300"
            }`}
          >
            {span.kind}
          </span>
          <span className="text-sm text-zinc-200">{span.name}</span>
          {span.status !== "success" && <StatusBadge status={span.status} />}
        </div>
        <div className="flex items-center gap-4 text-xs text-zinc-500">
          {span.gen_ai_request_model && <span>{span.gen_ai_request_model}</span>}
          {(span.input_tokens > 0 || span.output_tokens > 0) && (
            <span>
              {num(span.input_tokens)} / {num(span.output_tokens)} tok
            </span>
          )}
          {span.cost > 0 && <span>{usd(span.cost)}</span>}
          <span>{ms(span.latency_ms)}</span>
        </div>
      </div>
      <div className="mt-2 h-1.5 w-full rounded bg-zinc-800">
        <div
          className={`h-full rounded ${color}`}
          style={{ width: `${Math.max((span.latency_ms / maxLatency) * 100, 3)}%` }}
        />
      </div>
      {span.attributes && Boolean(span.attributes["gen_ai.prompt"]) && (
        <pre className="mt-2 max-h-24 overflow-auto rounded bg-black/40 p-2 text-[11px] text-zinc-400">
          {String(span.attributes["gen_ai.prompt"])}
        </pre>
      )}
    </li>
  );
}
