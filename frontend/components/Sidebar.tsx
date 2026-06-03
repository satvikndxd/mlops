"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/", label: "Dashboard", icon: "📊" },
  { href: "/traces", label: "Traces", icon: "🧵" },
  { href: "/agents", label: "Agents", icon: "🤖", soon: false },
  { href: "/costs", label: "Costs", icon: "💸" },
  { href: "/monitoring", label: "Monitoring", icon: "📈" },
  { href: "/alerts", label: "Alerts", icon: "🚨" },
  { href: "/incidents", label: "Incidents", icon: "🛠️", soon: true },
  { href: "/policies", label: "Policies", icon: "🛡️", soon: true },
  { href: "/settings", label: "Settings", icon: "⚙️" },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden w-60 shrink-0 flex-col border-r border-zinc-800 bg-zinc-900/40 p-4 md:flex">
      <div className="mb-8 flex items-center gap-2 px-2">
        <span className="text-2xl">🔥</span>
        <span className="text-lg font-semibold tracking-tight">AgentForge</span>
      </div>
      <nav className="flex flex-col gap-1">
        {NAV.map((item) => {
          const active =
            item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.soon ? "#" : item.href}
              className={`flex items-center justify-between rounded-lg px-3 py-2 text-sm transition ${
                active
                  ? "bg-brand/15 text-brand"
                  : "text-zinc-400 hover:bg-zinc-800/60 hover:text-zinc-100"
              } ${item.soon ? "cursor-not-allowed opacity-50" : ""}`}
            >
              <span className="flex items-center gap-2">
                <span>{item.icon}</span>
                {item.label}
              </span>
              {item.soon && (
                <span className="rounded bg-zinc-800 px-1.5 py-0.5 text-[10px] uppercase text-zinc-500">
                  soon
                </span>
              )}
            </Link>
          );
        })}
      </nav>
      <div className="mt-auto px-3 pt-6 text-[11px] leading-relaxed text-zinc-600">
        Phase 1A · Observability
        <br />
        Traces · Metrics · Costs
      </div>
    </aside>
  );
}
