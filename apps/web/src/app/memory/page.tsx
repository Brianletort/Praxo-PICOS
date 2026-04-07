"use client";

import { useState } from "react";

const SOURCE_COLORS: Record<string, string> = {
  mail: "bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-400",
  calendar: "bg-purple-100 text-purple-700 dark:bg-purple-900/50 dark:text-purple-400",
  screen: "bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-400",
  documents: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-400",
  vault: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-400",
};

const SAMPLE_RESULTS = [
  { id: "1", title: "Q2 Planning Meeting", source: "calendar", snippet: "Discussed roadmap priorities for Q2...", timestamp: "2026-04-07 14:00", score: 0.95 },
  { id: "2", title: "Re: Budget Approval", source: "mail", snippet: "The budget for the infrastructure project has been approved...", timestamp: "2026-04-07 11:23", score: 0.88 },
  { id: "3", title: "Architecture Decision Record", source: "vault", snippet: "We decided to use SQLite for local state and Qdrant for vector search...", timestamp: "2026-04-06 16:45", score: 0.82 },
  { id: "4", title: "Weekly Status Report", source: "documents", snippet: "Completed: Phase 1 backend services. Next: Web dashboard...", timestamp: "2026-04-05 09:00", score: 0.75 },
];

export default function MemoryPage() {
  const [query, setQuery] = useState("");
  const [results] = useState(SAMPLE_RESULTS);

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
          Memory
        </h1>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
          Search across all your ingested data
        </p>
      </div>

      <div className="mb-6">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search your memories..."
            className="flex-1 rounded-lg border border-zinc-300 bg-white px-4 py-2.5 text-sm text-zinc-900 placeholder:text-zinc-400 focus:border-zinc-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
          />
          <button className="rounded-lg bg-zinc-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300">
            Search
          </button>
        </div>
      </div>

      <div className="space-y-2">
        {results.map((result) => (
          <div
            key={result.id}
            className="rounded-xl border border-zinc-200 p-4 transition-colors hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-900"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
                    {result.title}
                  </h3>
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${SOURCE_COLORS[result.source] || SOURCE_COLORS.vault}`}>
                    {result.source}
                  </span>
                </div>
                <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
                  {result.snippet}
                </p>
              </div>
            </div>
            <div className="mt-2 flex items-center gap-3 text-xs text-zinc-500">
              <span>{result.timestamp}</span>
              <span>·</span>
              <span>Score: {(result.score * 100).toFixed(0)}%</span>
            </div>
          </div>
        ))}
      </div>

      {results.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16">
          <p className="text-4xl">🔍</p>
          <p className="mt-4 text-sm text-zinc-500 dark:text-zinc-400">
            No results found. Try a different search term.
          </p>
        </div>
      )}
    </div>
  );
}
