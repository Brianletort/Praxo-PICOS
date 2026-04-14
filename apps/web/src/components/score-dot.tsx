"use client";

import { cn } from "@/lib/utils";

interface ScoreDotProps {
  score: "green" | "yellow" | "red" | "none";
  size?: "sm" | "md";
  className?: string;
}

const DOT_COLORS = {
  green: "bg-emerald-500",
  yellow: "bg-amber-500",
  red: "bg-red-500",
  none: "bg-zinc-300 dark:bg-zinc-600",
} as const;

const SIZES = {
  sm: "h-2 w-2",
  md: "h-3 w-3",
} as const;

export function ScoreDot({ score, size = "md", className }: ScoreDotProps) {
  return (
    <span
      className={cn("inline-block rounded-full", DOT_COLORS[score], SIZES[size], className)}
      title={score !== "none" ? `Score: ${score}` : "No score"}
    />
  );
}
