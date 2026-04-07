"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { StatusCard } from "@/components/status-card";
import { api, type HealthResponse } from "@/lib/api";

export default function HomePage() {
  const router = useRouter();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.health()
      .then(setHealth)
      .catch(() => setHealth(null))
      .finally(() => setLoading(false));
  }, []);

  const overallStatus = health?.status === "ok" ? "ok" as const
    : health?.status === "degraded" ? "warning" as const
    : health ? "error" as const
    : "unknown" as const;

  const uptimeDetail = health
    ? `Uptime: ${Math.floor(health.uptime_seconds / 60)}m`
    : "Unable to reach API";

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
          Welcome to Praxo-PICOS
        </h1>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
          Your personal intelligence operating system
        </p>
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <p className="text-sm text-zinc-500 dark:text-zinc-400">Loading…</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <StatusCard
            title="System Status"
            status={overallStatus}
            detail={health ? `${health.status === "ok" ? "All services running" : health.status} · ${uptimeDetail}` : uptimeDetail}
          />
          <StatusCard
            title="Agent Zero"
            status="unknown"
            detail="Not configured yet"
            action={{ label: "Set up", onClick: () => router.push("/settings") }}
          />
          <StatusCard
            title="API Service"
            status={health ? "ok" : "error"}
            detail={health ? `${health.service} · ${uptimeDetail}` : "Cannot connect to API"}
            action={health ? undefined : { label: "Fix", onClick: () => router.push("/settings") }}
          />
          {health && Object.entries(health.dependencies).map(([name, dep]) => (
            <StatusCard
              key={name}
              title={name.charAt(0).toUpperCase() + name.slice(1)}
              status={dep.status === "ok" || dep.status === "healthy" ? "ok" : dep.error ? "error" : "unknown"}
              detail={dep.error ?? (dep.latency_ms != null ? `${dep.latency_ms}ms latency` : dep.status)}
              action={dep.error ? { label: "Fix", onClick: () => router.push("/settings") } : undefined}
            />
          ))}
        </div>
      )}

      <div className="mt-8">
        <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-100">
          Quick Actions
        </h2>
        <div className="mt-4 flex flex-wrap gap-3">
          {[
            { label: "Morning Brief", href: "/memory" },
            { label: "Search Memory", href: "/memory" },
            { label: "Check Health", href: "/health" },
            { label: "View Sources", href: "/sources" },
          ].map((action) => (
            <a
              key={action.label}
              href={action.href}
              className="rounded-lg border border-zinc-200 px-4 py-2 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-900"
            >
              {action.label}
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}
