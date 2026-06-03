"use client";

import { useCallback, useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface ApiKey {
  id: string;
  name: string;
  prefix: string;
  is_active: boolean;
  last_used_at: string | null;
  created_at: string;
}

interface AuditLog {
  id: string;
  actor: string;
  action: string;
  resource: string;
  status_code: number;
  ip: string | null;
  created_at: string;
}

export default function SettingsPage() {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [newKey, setNewKey] = useState<string | null>(null);
  const [name, setName] = useState("my-service-key");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [k, l] = await Promise.all([
        fetch(`${API_URL}/v1/auth/api-keys`, { cache: "no-store" }).then((r) => r.json()),
        fetch(`${API_URL}/v1/auth/audit-logs?limit=20`, { cache: "no-store" }).then((r) => r.json()),
      ]);
      setKeys(Array.isArray(k) ? k : []);
      setLogs(Array.isArray(l) ? l : []);
      setError(null);
    } catch {
      setError(`Could not reach the AgentForge API at ${API_URL}.`);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function createKey(e: React.FormEvent) {
    e.preventDefault();
    const res = await fetch(`${API_URL}/v1/auth/api-keys`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    const body = await res.json();
    setNewKey(body.api_key ?? null);
    await load();
  }

  async function revoke(id: string) {
    await fetch(`${API_URL}/v1/auth/api-keys/${id}`, { method: "DELETE" });
    await load();
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-900/50 bg-red-950/30 p-6 text-sm text-red-200">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-sm text-zinc-500">API keys, security, and audit trail.</p>
      </header>

      <section className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-5">
        <h2 className="mb-4 text-sm font-medium text-zinc-300">API keys</h2>
        <form onSubmit={createKey} className="mb-4 flex gap-2">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="flex-1 rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm"
            placeholder="Key name"
          />
          <button className="rounded-lg bg-brand px-4 py-2 text-sm font-medium text-black hover:bg-brand-dark">
            Create key
          </button>
        </form>
        {newKey && (
          <div className="mb-4 rounded-lg border border-emerald-900/50 bg-emerald-950/30 p-3 text-sm">
            <div className="text-emerald-300">Copy your key now — it won’t be shown again:</div>
            <code className="mt-1 block break-all font-mono text-emerald-200">{newKey}</code>
          </div>
        )}
        <ul className="divide-y divide-zinc-800/60">
          {keys.map((k) => (
            <li key={k.id} className="flex items-center justify-between py-2 text-sm">
              <span className="font-mono text-zinc-300">
                {k.prefix}••• · {k.name}
                {!k.is_active && <span className="ml-2 text-red-400">(revoked)</span>}
              </span>
              {k.is_active && (
                <button onClick={() => revoke(k.id)} className="text-xs text-red-400 hover:text-red-300">
                  revoke
                </button>
              )}
            </li>
          ))}
          {!keys.length && <li className="py-2 text-sm text-zinc-500">No API keys yet.</li>}
        </ul>
      </section>

      <section className="rounded-xl border border-zinc-800 bg-zinc-900/40">
        <h2 className="border-b border-zinc-800 px-5 py-4 text-sm font-medium text-zinc-300">
          Audit log
        </h2>
        <table className="w-full text-sm">
          <thead className="text-left text-xs uppercase text-zinc-500">
            <tr>
              <th className="px-5 py-2 font-medium">Actor</th>
              <th className="px-5 py-2 font-medium">Action</th>
              <th className="px-5 py-2 font-medium">Resource</th>
              <th className="px-5 py-2 font-medium">Status</th>
              <th className="px-5 py-2 font-medium">When</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((l) => (
              <tr key={l.id} className="border-t border-zinc-800/60">
                <td className="px-5 py-2 text-zinc-300">{l.actor}</td>
                <td className="px-5 py-2 text-zinc-400">{l.action}</td>
                <td className="px-5 py-2 font-mono text-xs text-zinc-400">{l.resource}</td>
                <td className="px-5 py-2 text-zinc-400">{l.status_code}</td>
                <td className="px-5 py-2 text-zinc-500">
                  {new Date(l.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
            {!logs.length && (
              <tr>
                <td colSpan={5} className="px-5 py-6 text-center text-zinc-500">
                  No audit entries yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </div>
  );
}
