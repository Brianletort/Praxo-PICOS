"use client";

import { useCallback, useEffect, useState } from "react";
import { StatusCard } from "@/components/status-card";
import { api, type HealthResponse, type DataFlowEntry } from "@/lib/api";

type CardStatus = "ok" | "warning" | "error" | "unknown";

function depStatus(s: string): CardStatus {
  if (s === "ok" || s === "healthy") return "ok";
  if (s === "degraded" || s === "warning") return "warning";
  if (s === "error" || s === "unhealthy") return "error";
  return "unknown";
}

function flowStatus(s: string): CardStatus {
  if (s === "ok" || s === "healthy") return "ok";
  if (s === "stale" || s === "warning") return "warning";
  if (s === "error") return "error";
  return "unknown";
}

function flowLabel(s: CardStatus): string {
  if (s === "ok") return "Healthy";
  if (s === "warning") return "Stale";
  if (s === "error") return "Error";
  return "Inactive";
}

function formatTime(iso: string | null): string {
  if (!iso) return "Never";
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins} min ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export default function HealthPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [dataFlow, setDataFlow] = useState<DataFlowEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [extractLoading, setExtractLoading] = useState(false);
  const [extractMessage, setExtractMessage] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    const [h, df] = await Promise.allSettled([api.health(), api.dataFlow()]);
    if (h.status === "fulfilled") setHealth(h.value);
    if (df.status === "fulfilled") setDataFlow(df.value.data_flow);
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  async function runExtraction() {
    setExtractLoading(true);
    setExtractMessage(null);
    try {
      const r = await api.extract.run();
      if (r.status === "error" && r.error) {
        setExtractMessage(`Extraction failed: ${r.error}`);
      } else {
        setExtractMessage(
          r.status === "completed" ? "Extraction completed." : `Status: ${r.status}`
        );
      }
    } catch (e) {
      setExtractMessage(e instanceof Error ? e.message : "Extraction request failed");
    } finally {
      setExtractLoading(false);
      await fetchAll();
    }
  }

  const services: { name: string; status: CardStatus; detail: string }[] = [];
  if (health) {
    services.push({
      name: "API Server",
      status: health.status === "ok" ? "ok" : health.status === "degraded" ? "warning" : "error",
      detail: `${health.status === "ok" ? "Healthy" : health.status} · uptime ${Math.floor(health.uptime_seconds / 60)}m`,
    });
    for (const [name, dep] of Object.entries(health.dependencies)) {
      services.push({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        status: depStatus(dep.status),
        detail: dep.error ?? (dep.latency_ms != null ? `${dep.latency_ms}ms latency` : dep.status),
      });
    }
    services.push({ name: "Web UI", status: "ok", detail: "This page · Port 3100" });
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
          Health Center
        </h1>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
          Monitor services, data flow, and system health
        </p>
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <p className="text-sm text-zinc-500 dark:text-zinc-400">Loading health data…</p>
        </div>
      ) : (
        <>
          <section className="mb-8">
            <h2 className="mb-4 text-lg font-medium text-zinc-900 dark:text-zinc-100">
              Services
            </h2>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {services.map((svc) => (
                <StatusCard
                  key={svc.name}
                  title={svc.name}
                  status={svc.status}
                  detail={svc.detail}
                />
              ))}
            </div>
          </section>

          <section className="mb-8">
            <h2 className="mb-4 text-lg font-medium text-zinc-900 dark:text-zinc-100">
              Data Flow
            </h2>
            <div className="overflow-hidden rounded-xl border border-zinc-200 dark:border-zinc-800">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900">
                    <th className="px-4 py-3 text-left font-medium text-zinc-600 dark:text-zinc-400">Source</th>
                    <th className="px-4 py-3 text-left font-medium text-zinc-600 dark:text-zinc-400">Status</th>
                    <th className="px-4 py-3 text-left font-medium text-zinc-600 dark:text-zinc-400">Last Sync</th>
                    <th className="px-4 py-3 text-right font-medium text-zinc-600 dark:text-zinc-400">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {dataFlow.map((src) => {
                    const st = flowStatus(src.status);
                    return (
                      <tr key={src.source} className="border-b border-zinc-100 last:border-0 dark:border-zinc-800">
                        <td className="px-4 py-3 font-medium capitalize text-zinc-900 dark:text-zinc-100">{src.source}</td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium ${
                            st === "ok"
                              ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300"
                              : st === "warning"
                              ? "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300"
                              : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"
                          }`}>
                            {flowLabel(st)}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-zinc-600 dark:text-zinc-400">{formatTime(src.last_record_at)}</td>
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={fetchAll}
                            className="text-xs font-medium text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                          >
                            Recheck
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                  {dataFlow.length === 0 && (
                    <tr>
                      <td colSpan={4} className="px-4 py-6 text-center text-sm text-zinc-500">
                        No data flow entries found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <section>
            <h2 className="mb-4 text-lg font-medium text-zinc-900 dark:text-zinc-100">
              Repair Actions
            </h2>
            <div className="flex flex-wrap gap-3">
              {[
                { label: "Restart All Services", variant: "primary" as const },
                { label: "Recheck Permissions", variant: "secondary" as const },
                { label: "Rebuild Index", variant: "secondary" as const },
                { label: "Export Diagnostics", variant: "secondary" as const },
              ].map((action) => (
                <button
                  key={action.label}
                  type="button"
                  onClick={action.label === "Restart All Services" ? fetchAll : undefined}
                  className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                    action.variant === "primary"
                      ? "bg-zinc-900 text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
                      : "border border-zinc-300 text-zinc-700 hover:bg-zinc-50 dark:border-zinc-600 dark:text-zinc-300 dark:hover:bg-zinc-900"
                  }`}
                >
                  {action.label}
                </button>
              ))}
              <button
                type="button"
                onClick={() => void runExtraction()}
                disabled={extractLoading}
                className="rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-50 disabled:opacity-50 dark:border-zinc-600 dark:text-zinc-300 dark:hover:bg-zinc-900"
              >
                {extractLoading ? "Running extraction…" : "Run Extraction"}
              </button>
            </div>
            {extractMessage && (
              <p className="mt-3 text-sm text-zinc-600 dark:text-zinc-400">{extractMessage}</p>
            )}
          </section>
        </>
      )}
    </div>
  );
}
