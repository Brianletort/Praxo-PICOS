"use client";

import { useState, useEffect } from "react";
import { useMode } from "@/lib/use-mode";
import { GlassCard } from "@/components/glass-card";
import { NarrativeCard } from "@/components/narrative-card";
import { PersonDetailModal } from "@/components/analytics/person-detail-modal";
import type { PersonDetailResponse, NarrativePayload } from "@/lib/analytics-types";

interface PersonListItem {
  id: string;
  name: string;
  email: string | null;
  organization: string | null;
  role: string | null;
  importance_level: number;
  narrative: NarrativePayload;
}

export default function PeoplePage() {
  const { isAdvanced } = useMode();
  const [people, setPeople] = useState<PersonListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/analytics/readiness")
      .then((r) => r.json())
      .then(async () => {
        const res = await fetch("/api/analytics/day?detail=full");
        const data = await res.json();
        if (data.people_needing_attention) {
          const items: PersonListItem[] = data.people_needing_attention.map(
            (p: { name: string; reason: string }, i: number) => ({
              id: `person_${i}`,
              name: p.name,
              email: null,
              organization: null,
              role: null,
              importance_level: 0,
              narrative: {
                headline: p.reason,
                bullets: [],
                trend: "stable",
                sentiment: "attention",
                available_depth: [],
              },
            })
          );
          setPeople(items);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-sm text-zinc-500">Loading people...</p>
      </div>
    );
  }

  if (people.length === 0) {
    return (
      <div className="mx-auto max-w-2xl py-8">
        <h1 className="mb-4 text-xl font-semibold text-zinc-900 dark:text-zinc-100">
          {isAdvanced ? "People Analytics" : "People"}
        </h1>
        <GlassCard>
          <p className="text-sm text-zinc-500">
            People will appear here as PICOS discovers contacts from your
            meetings, emails, and calendar. This happens automatically.
          </p>
        </GlassCard>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <h1 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100">
        {isAdvanced ? "People Analytics" : "People"}
      </h1>

      <div className="space-y-2">
        {people.map((person) => (
          <div
            key={person.id}
            className="cursor-pointer"
            onClick={() => setSelectedId(person.id)}
          >
            {isAdvanced ? (
              <GlassCard className="transition-shadow hover:shadow-md">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
                      {person.name}
                    </p>
                    <p className="text-xs text-zinc-500">
                      {person.organization || person.email || ""}
                      {person.role ? ` \u00B7 ${person.role}` : ""}
                    </p>
                  </div>
                  <TrendDot trend={person.narrative.sentiment} />
                </div>
              </GlassCard>
            ) : (
              <NarrativeCard narrative={person.narrative} compact />
            )}
          </div>
        ))}
      </div>

      {selectedId && (
        <PersonDetailModal
          personId={selectedId}
          onClose={() => setSelectedId(null)}
        />
      )}
    </div>
  );
}

function TrendDot({ trend }: { trend: string }) {
  const color =
    trend === "positive"
      ? "bg-emerald-400"
      : trend === "attention"
        ? "bg-amber-400"
        : "bg-zinc-300 dark:bg-zinc-600";
  return <span className={`h-3 w-3 rounded-full ${color}`} />;
}
