"use client";

import { useMode } from "@/lib/use-mode";
import { cn } from "@/lib/utils";

export function SimpleAdvancedToggle() {
  const { mode, toggleMode } = useMode();

  return (
    <button
      onClick={toggleMode}
      className={cn(
        "flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors",
        mode === "simple"
          ? "bg-zinc-100 text-zinc-600 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-700"
          : "bg-violet-100 text-violet-700 hover:bg-violet-200 dark:bg-violet-900/30 dark:text-violet-400 dark:hover:bg-violet-900/50"
      )}
      title={mode === "simple" ? "Switch to advanced mode" : "Switch to simple mode"}
    >
      {mode === "simple" ? (
        <>
          <svg className="h-3.5 w-3.5" viewBox="0 0 16 16" fill="currentColor">
            <circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" strokeWidth="1.5" />
            <circle cx="8" cy="8" r="2" />
          </svg>
          Simple
        </>
      ) : (
        <>
          <svg className="h-3.5 w-3.5" viewBox="0 0 16 16" fill="currentColor">
            <circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" strokeWidth="1.5" />
            <circle cx="5" cy="7" r="1.5" />
            <circle cx="11" cy="7" r="1.5" />
            <circle cx="8" cy="11" r="1.5" />
          </svg>
          Advanced
        </>
      )}
    </button>
  );
}
