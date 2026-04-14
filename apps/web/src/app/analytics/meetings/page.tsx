"use client";

import Link from "next/link";
import { useMeetings } from "@/lib/use-analytics";
import { useMode } from "@/lib/use-mode";
import { NarrativeCard } from "@/components/narrative-card";
import { ScoreDot } from "@/components/score-dot";
import { GlassCard } from "@/components/glass-card";
import { LearningPlaceholder } from "@/components/learning-placeholder";

export default function MeetingsPage() {
  const { isAdvanced } = useMode();
  const { data, loading } = useMeetings(4, isAdvanced ? "full" : "simple");

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-sm text-zinc-500">Loading meetings...</p>
      </div>
    );
  }

  if (!data || data.meetings.length === 0) {
    return (
      <div className="mx-auto max-w-2xl py-8">
        <h1 className="mb-4 text-xl font-semibold text-zinc-900 dark:text-zinc-100">
          Meetings
        </h1>
        <GlassCard>
          <p className="text-sm text-zinc-500">
            No meetings found yet. Once PICOS detects meetings from your calendar
            and screen activity, they will appear here with coaching insights.
          </p>
        </GlassCard>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100">
          {isAdvanced ? "Meeting Analytics" : "Meetings"}
        </h1>
        <span className="text-xs text-zinc-500">{data.total} total</span>
      </div>

      {data.availability.learning.map((lp, i) => (
        <LearningPlaceholder key={i} placeholder={lp} />
      ))}

      <div className="space-y-2">
        {data.meetings.map((meeting) => (
          <Link key={meeting.id} href={`/analytics/meetings/${meeting.id}`}>
            {isAdvanced ? (
              <GlassCard className="transition-shadow hover:shadow-md">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <ScoreDot score={meeting.score_dot} />
                    <div>
                      <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
                        {meeting.title ?? "Meeting"}
                      </p>
                      <p className="text-xs text-zinc-500">
                        {meeting.start_time
                          ? new Date(meeting.start_time).toLocaleString(undefined, {
                              month: "short",
                              day: "numeric",
                              hour: "numeric",
                              minute: "2-digit",
                            })
                          : ""}
                        {meeting.duration_minutes
                          ? ` \u00B7 ${Math.round(meeting.duration_minutes)}m`
                          : ""}
                        {meeting.attendee_count > 0
                          ? ` \u00B7 ${meeting.attendee_count} attendees`
                          : ""}
                      </p>
                    </div>
                  </div>
                  {meeting.intelligence_score != null && (
                    <span className="text-lg font-semibold text-zinc-700 dark:text-zinc-300">
                      {Math.round(meeting.intelligence_score * 100)}
                    </span>
                  )}
                </div>
              </GlassCard>
            ) : (
              <NarrativeCard narrative={meeting.narrative} compact />
            )}
          </Link>
        ))}
      </div>
    </div>
  );
}
