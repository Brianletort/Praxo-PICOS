"use client";

import { useEffect, useState } from "react";
import { useMode } from "@/lib/use-mode";
import { GlassCard } from "@/components/glass-card";
import { NarrativeCard } from "@/components/narrative-card";
import type { PersonDetailResponse } from "@/lib/analytics-types";

interface PersonDetailModalProps {
  personId: string;
  onClose: () => void;
}

export function PersonDetailModal({ personId, onClose }: PersonDetailModalProps) {
  const { isAdvanced } = useMode();
  const [data, setData] = useState<PersonDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const detail = isAdvanced ? "full" : "simple";
    fetch(`/api/analytics/person/${personId}?detail=${detail}`)
      .then((r) => r.json())
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [personId, isAdvanced]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="mx-4 w-full max-w-lg rounded-2xl border border-zinc-200/60 bg-white p-6 shadow-xl dark:border-zinc-700/40 dark:bg-zinc-900">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
            {data?.name || "Person"}
          </h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 dark:hover:bg-zinc-800"
          >
            <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
            </svg>
          </button>
        </div>

        {loading && <p className="text-sm text-zinc-500">Loading...</p>}

        {data && !("error" in data) && (
          <div className="space-y-3">
            {data.email && (
              <p className="text-xs text-zinc-500">{data.email}</p>
            )}
            {data.organization && (
              <p className="text-xs text-zinc-500">
                {data.organization}
                {data.role ? ` \u00B7 ${data.role}` : ""}
              </p>
            )}

            <NarrativeCard narrative={data.narrative} />

            {data.top_insights.length > 0 && (
              <GlassCard title="Insights">
                <ul className="space-y-2">
                  {data.top_insights.map((insight, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <span
                        className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${
                          insight.actionable
                            ? "bg-amber-400"
                            : "bg-zinc-300 dark:bg-zinc-600"
                        }`}
                      />
                      <div>
                        <p className="font-medium text-zinc-800 dark:text-zinc-200">
                          {insight.headline}
                        </p>
                        {insight.detail && (
                          <p className="text-xs text-zinc-500">{insight.detail}</p>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              </GlassCard>
            )}

            {isAdvanced && data.intelligence && (
              <>
                {data.intelligence.communication_dynamic && (
                  <GlassCard title="Communication Style" collapsible>
                    <MetricsView
                      data={data.intelligence.communication_dynamic as Record<string, unknown>}
                    />
                  </GlassCard>
                )}
                {data.intelligence.relationship_dynamics && (
                  <GlassCard title="Relationship Dynamics" collapsible>
                    <MetricsView
                      data={data.intelligence.relationship_dynamics as Record<string, unknown>}
                    />
                  </GlassCard>
                )}
                {data.intelligence.style_profile && (
                  <GlassCard title="Style Profile" collapsible defaultCollapsed>
                    <MetricsView
                      data={data.intelligence.style_profile as Record<string, unknown>}
                    />
                  </GlassCard>
                )}
              </>
            )}
          </div>
        )}

        {data && "error" in data && (
          <p className="text-sm text-zinc-500">Person not found.</p>
        )}
      </div>
    </div>
  );
}

function MetricsView({ data }: { data: Record<string, unknown> }) {
  return (
    <div className="space-y-1">
      {Object.entries(data).map(([key, value]) => {
        if (typeof value === "object" && value !== null) return null;
        return (
          <div key={key} className="flex justify-between text-sm">
            <span className="text-zinc-500">{key.replace(/_/g, " ")}</span>
            <span className="font-medium text-zinc-800 dark:text-zinc-200">
              {typeof value === "number"
                ? Number.isInteger(value)
                  ? value
                  : (value as number).toFixed(2)
                : String(value ?? "")}
            </span>
          </div>
        );
      })}
    </div>
  );
}
