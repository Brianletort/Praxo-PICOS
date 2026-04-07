"use client";

import { StatusCard } from "@/components/status-card";

export default function HomePage() {
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

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatusCard
          title="System Status"
          status="ok"
          detail="All services running"
        />
        <StatusCard
          title="Agent Zero"
          status="unknown"
          detail="Not configured yet"
          action={{ label: "Set up", onClick: () => {} }}
        />
        <StatusCard
          title="Last Memory Sync"
          status="ok"
          detail="Just now"
        />
        <StatusCard
          title="Permissions"
          status="warning"
          detail="Full Disk Access needed for Mail"
          action={{ label: "Fix", onClick: () => {} }}
        />
        <StatusCard
          title="Updates"
          status="ok"
          detail="You're on the latest version"
        />
      </div>

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
