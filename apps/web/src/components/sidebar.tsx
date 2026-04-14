"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useMode } from "@/lib/use-mode";

const NAV_ITEMS = [
  { href: "/", label: "Home", icon: "🏠" },
  { href: "/analytics", label: "Insights", advancedLabel: "Analytics", icon: "✨" },
  { href: "/assistant", label: "Assistant", icon: "💬" },
  { href: "/memory", label: "Memory", icon: "🧠" },
  { href: "/sources", label: "Sources", icon: "📥" },
  { href: "/health", label: "Health", icon: "🩺" },
  { href: "/settings", label: "Settings", icon: "⚙️" },
] as const;

export function Sidebar() {
  const pathname = usePathname();
  const { isAdvanced } = useMode();

  return (
    <aside className="flex w-56 flex-col border-r border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-950">
      <div className="flex h-14 items-center gap-2 border-b border-zinc-200 px-4 dark:border-zinc-800">
        <span className="text-lg font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
          Praxo-PICOS
        </span>
      </div>

      <nav className="flex flex-1 flex-col gap-1 p-2">
        {NAV_ITEMS.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);

          const displayLabel =
            isAdvanced && "advancedLabel" in item && item.advancedLabel
              ? item.advancedLabel
              : item.label;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-zinc-200 text-zinc-900 dark:bg-zinc-800 dark:text-zinc-100"
                  : "text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-900 dark:hover:text-zinc-100"
              }`}
            >
              <span className="text-base">{item.icon}</span>
              {displayLabel}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-zinc-200 p-3 dark:border-zinc-800">
        <div className="flex items-center gap-2 text-xs text-zinc-500 dark:text-zinc-500">
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          System running
        </div>
      </div>
    </aside>
  );
}
