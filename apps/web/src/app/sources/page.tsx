"use client";

import { useCallback, useEffect, useState } from "react";
import { api, type SourceStatus } from "@/lib/api";

const SOURCE_ICONS: Record<string, string> = {
  mail: "📧",
  calendar: "📅",
  screen: "🖥️",
  documents: "📁",
  vault: "📓",
};

function formatLastSync(iso: string | undefined): string {
  if (!iso) return "Never";
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins} min ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export default function SourcesPage() {
  const [sources, setSources] = useState<SourceStatus[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchSources = useCallback(async () => {
    try {
      const data = await api.sources.list();
      setSources(data.sources);
    } catch {
      setSources([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSources();
  }, [fetchSources]);

  async function setSourceEnabled(name: string, checked: boolean) {
    const previous = sources.find((s) => s.name === name)?.enabled ?? false;
    setSources((list) =>
      list.map((s) => (s.name === name ? { ...s, enabled: checked } : s))
    );
    try {
      await api.config.patch({ [`${name}_enabled`]: checked });
    } catch {
      setSources((list) =>
        list.map((s) => (s.name === name ? { ...s, enabled: previous } : s))
      );
    }
  }

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

      {loading ? (
        <div className="flex justify-center py-16">
          <p className="text-sm text-zinc-500 dark:text-zinc-400">Loading sources…</p>
        </div>
      ) : sources.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16">
          <p className="text-sm text-zinc-500 dark:text-zinc-400">No sources configured.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {sources.map((src) => (
            <div
              key={src.name}
              className="flex items-center justify-between rounded-xl border border-zinc-200 p-4 dark:border-zinc-800"
            >
              <div className="flex items-center gap-4">
                <span className="text-2xl">{SOURCE_ICONS[src.name] ?? "📦"}</span>
                <div>
                  <h3 className="text-sm font-medium capitalize text-zinc-900 dark:text-zinc-100">
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
                    <span>{(src.records_count ?? 0).toLocaleString()} records</span>
                    <span>·</span>
                    <span>Last sync: {formatLastSync(src.last_extraction)}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <label className="relative inline-flex cursor-pointer items-center">
                  <input
                    type="checkbox"
                    checked={src.enabled}
                    onChange={(e) => void setSourceEnabled(src.name, e.target.checked)}
                    className="peer sr-only"
                  />
                  <div className="h-6 w-11 rounded-full bg-zinc-200 after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:bg-white after:transition-all peer-checked:bg-emerald-500 peer-checked:after:translate-x-full dark:bg-zinc-700" />
                </label>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
