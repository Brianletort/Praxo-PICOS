"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useMode } from "@/lib/use-mode";
import { SimpleAdvancedToggle } from "@/components/simple-advanced-toggle";

const TABS = [
  { href: "/analytics", label: "Your Day", simpleLabel: "Today" },
  { href: "/analytics/meetings", label: "Meetings", simpleLabel: "Meetings" },
  { href: "/analytics/people", label: "People", simpleLabel: "People" },
] as const;

export default function AnalyticsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const { isAdvanced } = useMode();

  return (
    <div className="flex flex-1 flex-col">
      <div className="flex items-center justify-between border-b border-zinc-200 px-6 py-3 dark:border-zinc-800">
        <div className="flex items-center gap-1">
          {TABS.map((tab) => {
            const isActive =
              tab.href === "/analytics"
                ? pathname === "/analytics"
                : pathname.startsWith(tab.href);

            return (
              <Link
                key={tab.href}
                href={tab.href}
                className={cn(
                  "rounded-lg px-3 py-1.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                    : "text-zinc-500 hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:hover:text-zinc-100"
                )}
              >
                {isAdvanced ? tab.label : tab.simpleLabel}
              </Link>
            );
          })}
        </div>
        <SimpleAdvancedToggle />
      </div>
      <div className="flex-1 overflow-y-auto p-6">{children}</div>
    </div>
  );
}
