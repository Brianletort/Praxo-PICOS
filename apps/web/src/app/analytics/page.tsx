"use client";

import { useDaySummary, useReadiness } from "@/lib/use-analytics";
import { useMode } from "@/lib/use-mode";
import { NarrativeCard } from "@/components/narrative-card";
import { GlassCard } from "@/components/glass-card";
import { LearningPlaceholder } from "@/components/learning-placeholder";

export default function AnalyticsDayPage() {
  const { data, loading } = useDaySummary();
  const { data: readiness } = useReadiness();
  const { isAdvanced } = useMode();

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-sm text-zinc-500">Loading your day...</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="mx-auto max-w-2xl space-y-4 py-8">
        <h1 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100">
          Your Day
        </h1>
        <GlassCard>
          <p className="text-sm text-zinc-500">
            PICOS is getting to know you. Connect your data sources in Settings to get started.
          </p>
        </GlassCard>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <h1 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100">
        {isAdvanced ? "Daily Intelligence" : "Your Day"}
      </h1>

      <NarrativeCard narrative={data.narrative} />

      {data.top_insights.length > 0 && (
        <GlassCard title={isAdvanced ? "Top Insights" : undefined}>
          <ul className="space-y-2">
            {data.top_insights.map((insight, i) => (
              <li key={i} className="flex items-start gap-2">
                {insight.actionable && (
                  <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-amber-400" />
                )}
                {!insight.actionable && (
                  <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-zinc-300 dark:bg-zinc-600" />
                )}
                <div>
                  <p className="text-sm font-medium text-zinc-800 dark:text-zinc-200">
                    {insight.headline}
                  </p>
                  {isAdvanced && insight.detail && (
                    <p className="text-xs text-zinc-500">{insight.detail}</p>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </GlassCard>
      )}

      {data.people_needing_attention.length > 0 && (
        <GlassCard title="People needing attention">
          <ul className="space-y-2">
            {data.people_needing_attention.map((person, i) => (
              <li key={i} className="flex items-center gap-2 text-sm">
                <span className="h-2 w-2 rounded-full bg-amber-400" />
                <span className="font-medium text-zinc-800 dark:text-zinc-200">
                  {person.name}
                </span>
                <span className="text-zinc-500">&mdash; {person.reason}</span>
              </li>
            ))}
          </ul>
        </GlassCard>
      )}

      {readiness?.readiness &&
        Object.entries(readiness.readiness).map(([domain, info]) =>
          info.learning.map((lp, i) => (
            <LearningPlaceholder key={`${domain}-${i}`} placeholder={lp} />
          ))
        )}

      {isAdvanced && data.meetings && data.meetings.length > 0 && (
        <GlassCard title="Meeting Breakdown" collapsible defaultCollapsed>
          <ul className="space-y-1">
            {data.meetings.map((m) => (
              <li key={m.id} className="text-sm text-zinc-600 dark:text-zinc-400">
                {m.title ?? "Meeting"} &mdash; score: {m.intelligence_score ?? "n/a"}
              </li>
            ))}
          </ul>
        </GlassCard>
      )}
    </div>
  );
}
