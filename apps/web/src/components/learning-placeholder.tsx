"use client";

import { cn } from "@/lib/utils";
import type { LearningPlaceholder as LPType } from "@/lib/analytics-types";

interface LearningPlaceholderProps {
  placeholder: LPType;
  className?: string;
}

export function LearningPlaceholder({ placeholder, className }: LearningPlaceholderProps) {
  const progress = Math.min(100, Math.max(0, placeholder.progress));

  return (
    <div
      className={cn(
        "rounded-xl border border-dashed border-zinc-200 bg-zinc-50/50 p-4",
        "dark:border-zinc-700 dark:bg-zinc-900/30",
        className
      )}
    >
      <div className="flex items-start gap-3">
        <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-zinc-100 dark:bg-zinc-800">
          <svg className="h-3.5 w-3.5 text-zinc-400" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 1a7 7 0 100 14A7 7 0 008 1zm0 2.5a1.25 1.25 0 110 2.5 1.25 1.25 0 010-2.5zM6.75 7.5h2.5v5h-2.5v-5z" />
          </svg>
        </div>
        <div className="flex-1">
          <p className="text-sm text-zinc-500 dark:text-zinc-400">{placeholder.message}</p>
          {progress > 0 && (
            <div className="mt-2 h-1 w-full overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-700">
              <div
                className="h-full rounded-full bg-violet-400 transition-all dark:bg-violet-500"
                style={{ width: `${progress}%` }}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
