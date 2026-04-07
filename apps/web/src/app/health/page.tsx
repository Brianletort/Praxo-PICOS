import { StatusCard } from "@/components/status-card";

const SERVICES = [
  { name: "API Server", port: 8865, status: "ok" as const, detail: "Healthy, 99.9% uptime" },
  { name: "Workers", port: null, status: "ok" as const, detail: "3 extractors active" },
  { name: "Qdrant", port: 6733, status: "ok" as const, detail: "Connected, 1.2k vectors" },
  { name: "Web UI", port: 3100, status: "ok" as const, detail: "This page" },
  { name: "Agent Zero", port: 50001, status: "unknown" as const, detail: "Not configured" },
  { name: "MCP Server", port: 8870, status: "ok" as const, detail: "5 tools registered" },
];

const DATA_SOURCES = [
  { name: "Mail", status: "ok" as const, lastSync: "2 min ago" },
  { name: "Calendar", status: "ok" as const, lastSync: "5 min ago" },
  { name: "Screen", status: "unknown" as const, lastSync: "Never" },
  { name: "Documents", status: "warning" as const, lastSync: "1 hour ago" },
  { name: "Vault", status: "ok" as const, lastSync: "10 min ago" },
];

export default function HealthPage() {
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

      <section className="mb-8">
        <h2 className="mb-4 text-lg font-medium text-zinc-900 dark:text-zinc-100">
          Services
        </h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {SERVICES.map((svc) => (
            <StatusCard
              key={svc.name}
              title={svc.name}
              status={svc.status}
              detail={`${svc.detail}${svc.port ? ` · Port ${svc.port}` : ""}`}
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
              {DATA_SOURCES.map((src) => (
                <tr key={src.name} className="border-b border-zinc-100 last:border-0 dark:border-zinc-800">
                  <td className="px-4 py-3 font-medium text-zinc-900 dark:text-zinc-100">{src.name}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium ${
                      src.status === "ok"
                        ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300"
                        : src.status === "warning"
                        ? "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300"
                        : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"
                    }`}>
                      {src.status === "ok" ? "Healthy" : src.status === "warning" ? "Stale" : "Inactive"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-zinc-600 dark:text-zinc-400">{src.lastSync}</td>
                  <td className="px-4 py-3 text-right">
                    <button className="text-xs font-medium text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300">
                      Recheck
                    </button>
                  </td>
                </tr>
              ))}
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
            { label: "Restart All Services", variant: "primary" },
            { label: "Recheck Permissions", variant: "secondary" },
            { label: "Rebuild Index", variant: "secondary" },
            { label: "Export Diagnostics", variant: "secondary" },
          ].map((action) => (
            <button
              key={action.label}
              className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                action.variant === "primary"
                  ? "bg-zinc-900 text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
                  : "border border-zinc-300 text-zinc-700 hover:bg-zinc-50 dark:border-zinc-600 dark:text-zinc-300 dark:hover:bg-zinc-900"
              }`}
            >
              {action.label}
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}
