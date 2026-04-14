"use client";

import { use } from "react";
import Link from "next/link";
import { useMeeting } from "@/lib/use-analytics";
import { useMode } from "@/lib/use-mode";
import { NarrativeCard } from "@/components/narrative-card";
import { GlassCard } from "@/components/glass-card";
import { ScoreDot } from "@/components/score-dot";

export default function MeetingDetailPage({
  params,
}: {
  params: Promise<{ meetingId: string }>;
}) {
  const { meetingId } = use(params);
  const { isAdvanced } = useMode();
  const { data, loading } = useMeeting(meetingId, isAdvanced ? "full" : "simple");

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-sm text-zinc-500">Loading meeting...</p>
      </div>
    );
  }

  if (!data || data.id === undefined) {
    return (
      <div className="mx-auto max-w-2xl py-8">
        <Link
          href="/analytics/meetings"
          className="text-sm text-zinc-500 hover:text-zinc-700"
        >
          &larr; Back to meetings
        </Link>
        <p className="mt-4 text-sm text-zinc-500">Meeting not found.</p>
      </div>
    );
  }

  const scoreDot = data.intelligence_score
    ? data.intelligence_score >= 0.75
      ? "green" as const
      : data.intelligence_score >= 0.5
        ? "yellow" as const
        : "red" as const
    : "none" as const;

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <Link
        href="/analytics/meetings"
        className="text-sm text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300"
      >
        &larr; Back to meetings
      </Link>

      <div className="flex items-center gap-3">
        <ScoreDot score={scoreDot} size="md" />
        <div>
          <h1 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100">
            {data.title ?? "Meeting"}
          </h1>
          <p className="text-sm text-zinc-500">
            {data.start_time
              ? new Date(data.start_time).toLocaleString(undefined, {
                  weekday: "short",
                  month: "short",
                  day: "numeric",
                  hour: "numeric",
                  minute: "2-digit",
                })
              : ""}
            {data.duration_minutes
              ? ` \u00B7 ${Math.round(data.duration_minutes)} minutes`
              : ""}
          </p>
        </div>
      </div>

      <NarrativeCard narrative={data.narrative} />

      {data.top_insights.length > 0 && (
        <GlassCard title={isAdvanced ? "Top Insights" : "Coaching"}>
          <ul className="space-y-2">
            {data.top_insights.map((insight, i) => (
              <li key={i} className="flex items-start gap-2">
                <span
                  className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${
                    insight.actionable ? "bg-amber-400" : "bg-zinc-300 dark:bg-zinc-600"
                  }`}
                />
                <div>
                  <p className="text-sm font-medium text-zinc-800 dark:text-zinc-200">
                    {insight.headline}
                  </p>
                  {(isAdvanced || insight.actionable) && insight.detail && (
                    <p className="text-xs text-zinc-500">{insight.detail}</p>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </GlassCard>
      )}

      {data.summary && (
        <GlassCard title="Summary">
          <p className="text-sm text-zinc-600 dark:text-zinc-400">{data.summary}</p>
        </GlassCard>
      )}

      {isAdvanced && data.intelligence && (
        <>
          {data.intelligence.scorecard && (
            <GlassCard title="Scorecard" collapsible>
              <ScorecardView data={data.intelligence.scorecard as Record<string, unknown>} />
            </GlassCard>
          )}
          {data.intelligence.delivery_metrics && (
            <GlassCard title="Delivery Metrics" collapsible defaultCollapsed>
              <MetricsTable data={data.intelligence.delivery_metrics as Record<string, unknown>} />
            </GlassCard>
          )}
          {data.intelligence.attention && (
            <GlassCard title="Attention & Focus" collapsible defaultCollapsed>
              <MetricsTable data={data.intelligence.attention as Record<string, unknown>} />
            </GlassCard>
          )}
          {data.intelligence.body_language && (
            <GlassCard title="Body Language" collapsible defaultCollapsed>
              <MetricsTable data={data.intelligence.body_language as Record<string, unknown>} />
            </GlassCard>
          )}
          {data.intelligence.power_dynamics && (
            <GlassCard title="Power Dynamics" collapsible defaultCollapsed>
              <MetricsTable data={data.intelligence.power_dynamics as Record<string, unknown>} />
            </GlassCard>
          )}
        </>
      )}
    </div>
  );
}

function ScorecardView({ data }: { data: Record<string, unknown> }) {
  const categories = ["delivery", "engagement", "presence", "preparation"];
  const overall = data.overall_score as number | undefined;

  return (
    <div className="space-y-3">
      {overall != null && (
        <div className="text-center">
          <span className="text-3xl font-bold text-zinc-900 dark:text-zinc-100">
            {Math.round(overall * 100)}
          </span>
          <p className="text-xs text-zinc-500">Overall Score</p>
        </div>
      )}
      <div className="grid grid-cols-2 gap-3">
        {categories.map((cat) => {
          const section = data[cat] as Record<string, unknown> | undefined;
          const score = section?.score as number | undefined;
          if (score == null) return null;
          return (
            <div key={cat} className="rounded-lg bg-zinc-50 p-3 dark:bg-zinc-800/50">
              <p className="text-xs font-medium capitalize text-zinc-500">{cat}</p>
              <p className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                {Math.round(score * 100)}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function MetricsTable({ data }: { data: Record<string, unknown> }) {
  return (
    <div className="space-y-1">
      {Object.entries(data).map(([key, value]) => (
        <div key={key} className="flex justify-between text-sm">
          <span className="text-zinc-500">{key.replace(/_/g, " ")}</span>
          <span className="font-medium text-zinc-800 dark:text-zinc-200">
            {typeof value === "number"
              ? Number.isInteger(value)
                ? value
                : value.toFixed(2)
              : String(value)}
          </span>
        </div>
      ))}
    </div>
  );
}
