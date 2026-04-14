"use client";

import { cn } from "@/lib/utils";

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
  title?: string;
}

export function GlassCard({
  children,
  className,
  collapsible = false,
  defaultCollapsed = false,
  title,
}: GlassCardProps) {
  const [collapsed, setCollapsed] = useState(defaultCollapsed);

  return (
    <div
      className={cn(
        "rounded-2xl border border-zinc-200/60 bg-white/80 p-5 shadow-sm backdrop-blur-sm",
        "dark:border-zinc-700/40 dark:bg-zinc-900/60",
        className
      )}
    >
      {title && (
        <div
          className={cn(
            "flex items-center justify-between",
            collapsible && "cursor-pointer select-none"
          )}
          onClick={collapsible ? () => setCollapsed(!collapsed) : undefined}
        >
          <h3 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300">
            {title}
          </h3>
          {collapsible && (
            <ChevronIcon collapsed={collapsed} />
          )}
        </div>
      )}
      {(!collapsible || !collapsed) && (
        <div className={title ? "mt-3" : ""}>{children}</div>
      )}
    </div>
  );
}

function ChevronIcon({ collapsed }: { collapsed: boolean }) {
  return (
    <svg
      className={cn(
        "h-4 w-4 text-zinc-400 transition-transform",
        !collapsed && "rotate-180"
      )}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
    </svg>
  );
}

import { useState } from "react";
