"use client";

import { cn } from "@/lib/utils";
import type { NarrativePayload } from "@/lib/analytics-types";

interface NarrativeCardProps {
  narrative: NarrativePayload;
  className?: string;
  onClick?: () => void;
  compact?: boolean;
}

const SENTIMENT_STYLES = {
  positive: "border-l-emerald-400",
  neutral: "border-l-zinc-300 dark:border-l-zinc-600",
  attention: "border-l-amber-400",
} as const;

const TREND_LABELS: Record<string, { label: string; icon: string }> = {
  improving: { label: "Improving", icon: "trending_up" },
  stable: { label: "Stable", icon: "trending_flat" },
  declining: { label: "Declining", icon: "trending_down" },
};

export function NarrativeCard({
  narrative,
  className,
  onClick,
  compact = false,
}: NarrativeCardProps) {
  const sentimentStyle =
    SENTIMENT_STYLES[narrative.sentiment as keyof typeof SENTIMENT_STYLES] ??
    SENTIMENT_STYLES.neutral;

  return (
    <div
      className={cn(
        "rounded-xl border border-zinc-200/60 border-l-4 bg-white/80 p-4 shadow-sm backdrop-blur-sm",
        "dark:border-zinc-700/40 dark:bg-zinc-900/60",
        sentimentStyle,
        onClick && "cursor-pointer transition-shadow hover:shadow-md",
        className
      )}
      onClick={onClick}
    >
      <p
        className={cn(
          "font-semibold text-zinc-900 dark:text-zinc-100",
          compact ? "text-sm" : "text-base"
        )}
      >
        {narrative.headline}
      </p>

      {narrative.bullets.length > 0 && !compact && (
        <ul className="mt-2 space-y-1">
          {narrative.bullets.map((bullet, i) => (
            <li
              key={i}
              className="flex items-start gap-2 text-sm text-zinc-600 dark:text-zinc-400"
            >
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-zinc-300 dark:bg-zinc-600" />
              {bullet}
            </li>
          ))}
        </ul>
      )}

      <div className="mt-2 flex items-center gap-3">
        <TrendBadge trend={narrative.trend} />
        {narrative.available_depth.length > 0 && (
          <span className="text-xs text-zinc-400 dark:text-zinc-500">
            {narrative.available_depth.length} detail{narrative.available_depth.length !== 1 ? "s" : ""} available
          </span>
        )}
      </div>
    </div>
  );
}

function TrendBadge({ trend }: { trend: string }) {
  const info = TREND_LABELS[trend];
  if (!info) return null;

  const colorClass =
    trend === "improving"
      ? "text-emerald-600 dark:text-emerald-400"
      : trend === "declining"
        ? "text-amber-600 dark:text-amber-400"
        : "text-zinc-500";

  return (
    <span className={cn("flex items-center gap-1 text-xs font-medium", colorClass)}>
      <TrendArrow trend={trend} />
      {info.label}
    </span>
  );
}

function TrendArrow({ trend }: { trend: string }) {
  if (trend === "improving") {
    return (
      <svg className="h-3 w-3" viewBox="0 0 12 12" fill="currentColor">
        <path d="M6 2l4 4H7v4H5V6H2l4-4z" />
      </svg>
    );
  }
  if (trend === "declining") {
    return (
      <svg className="h-3 w-3" viewBox="0 0 12 12" fill="currentColor">
        <path d="M6 10l-4-4h3V2h2v4h3l-4 4z" />
      </svg>
    );
  }
  return (
    <svg className="h-3 w-3" viewBox="0 0 12 12" fill="currentColor">
      <path d="M1 6h10" stroke="currentColor" strokeWidth="2" />
    </svg>
  );
}
