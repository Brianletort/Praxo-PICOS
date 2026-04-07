"use client";

const SOURCES = [
  { name: "Mail", icon: "📧", enabled: true, status: "ok" as const, lastSync: "2 min ago", records: 1247, permission: "granted" },
  { name: "Calendar", icon: "📅", enabled: true, status: "ok" as const, lastSync: "5 min ago", records: 89, permission: "granted" },
  { name: "Screen Capture", icon: "🖥️", enabled: false, status: "unknown" as const, lastSync: "Never", records: 0, permission: "not_requested" },
  { name: "Documents", icon: "📁", enabled: false, status: "unknown" as const, lastSync: "Never", records: 0, permission: "granted" },
  { name: "Obsidian Vault", icon: "📓", enabled: true, status: "ok" as const, lastSync: "10 min ago", records: 342, permission: "granted" },
];

export default function SourcesPage() {
  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
          Data Sources
        </h1>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
          Manage where your memories come from
        </p>
      </div>

      <div className="space-y-3">
        {SOURCES.map((src) => (
          <div
            key={src.name}
            className="flex items-center justify-between rounded-xl border border-zinc-200 p-4 dark:border-zinc-800"
          >
            <div className="flex items-center gap-4">
              <span className="text-2xl">{src.icon}</span>
              <div>
                <h3 className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
                  {src.name}
                </h3>
                <div className="mt-0.5 flex items-center gap-2 text-xs text-zinc-500">
                  <span className={`inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-xs ${
                    src.status === "ok"
                      ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-400"
                      : "bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-500"
                  }`}>
                    {src.status === "ok" ? "Active" : "Inactive"}
                  </span>
                  <span>·</span>
                  <span>{src.records.toLocaleString()} records</span>
                  <span>·</span>
                  <span>Last sync: {src.lastSync}</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {src.permission === "not_requested" && (
                <button className="rounded-lg border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-400">
                  Grant Permission
                </button>
              )}
              <label className="relative inline-flex cursor-pointer items-center">
                <input
                  type="checkbox"
                  defaultChecked={src.enabled}
                  className="peer sr-only"
                />
                <div className="h-6 w-11 rounded-full bg-zinc-200 after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:bg-white after:transition-all peer-checked:bg-emerald-500 peer-checked:after:translate-x-full dark:bg-zinc-700" />
              </label>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
