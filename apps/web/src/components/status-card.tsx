"use client";

interface StatusCardProps {
  title: string;
  status: "ok" | "warning" | "error" | "unknown";
  detail?: string;
  action?: { label: string; onClick: () => void };
}

const STATUS_STYLES = {
  ok: "border-emerald-200 bg-emerald-50 dark:border-emerald-800 dark:bg-emerald-950",
  warning: "border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-950",
  error: "border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950",
  unknown: "border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900",
} as const;

const STATUS_DOTS = {
  ok: "bg-emerald-500",
  warning: "bg-amber-500",
  error: "bg-red-500",
  unknown: "bg-zinc-400",
} as const;

export function StatusCard({ title, status, detail, action }: StatusCardProps) {
  return (
    <div className={`rounded-xl border p-4 ${STATUS_STYLES[status]}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={`h-2.5 w-2.5 rounded-full ${STATUS_DOTS[status]}`} />
          <h3 className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
            {title}
          </h3>
        </div>
        {action && (
          <button
            onClick={action.onClick}
            className="text-xs font-medium text-zinc-600 underline hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"
          >
            {action.label}
          </button>
        )}
      </div>
      {detail && (
        <p className="mt-1 text-xs text-zinc-600 dark:text-zinc-400">{detail}</p>
      )}
    </div>
  );
}
