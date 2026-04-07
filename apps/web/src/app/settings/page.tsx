"use client";

import { useState, type ReactNode } from "react";

type Mode = "basic" | "advanced";

export default function SettingsPage() {
  const [mode, setMode] = useState<Mode>("basic");

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
            Settings
          </h1>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            Configure your personal intelligence system
          </p>
        </div>
        <div className="flex rounded-lg border border-zinc-300 dark:border-zinc-600">
          {(["basic", "advanced"] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`px-4 py-1.5 text-sm font-medium capitalize transition-colors ${
                mode === m
                  ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                  : "text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"
              } ${m === "basic" ? "rounded-l-lg" : "rounded-r-lg"}`}
            >
              {m}
            </button>
          ))}
        </div>
      </div>

      <div className="max-w-2xl space-y-6">
        <SettingsSection title="Memory Folder">
          <div className="flex items-center gap-3">
            <input
              type="text"
              defaultValue="~/Documents/Praxo-PICOS"
              className="flex-1 rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
            />
            <button className="rounded-lg border border-zinc-300 px-3 py-2 text-sm font-medium dark:border-zinc-600 dark:text-zinc-300">
              Browse
            </button>
          </div>
          <p className="mt-1 text-xs text-zinc-500">
            Recommended — Where your memories and summaries are stored
          </p>
        </SettingsSection>

        <SettingsSection title="Data Sources">
          {["Mail", "Calendar", "Screen Capture", "Documents", "Obsidian Vault"].map(
            (source) => (
              <label key={source} className="flex items-center justify-between py-2">
                <span className="text-sm text-zinc-700 dark:text-zinc-300">{source}</span>
                <input
                  type="checkbox"
                  defaultChecked={["Mail", "Calendar"].includes(source)}
                  className="h-4 w-4 rounded border-zinc-300 text-zinc-900 dark:border-zinc-600"
                />
              </label>
            )
          )}
        </SettingsSection>

        <SettingsSection title="AI Provider">
          <select className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100">
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="openrouter">OpenRouter</option>
          </select>
          <button className="mt-2 rounded-lg border border-zinc-300 px-3 py-1.5 text-xs font-medium text-zinc-600 dark:border-zinc-600 dark:text-zinc-400">
            Test Connection
          </button>
        </SettingsSection>

        {mode === "advanced" && (
          <>
            <SettingsSection title="Ports">
              {[
                { label: "API", defaultValue: "8865" },
                { label: "Web", defaultValue: "3100" },
                { label: "MCP", defaultValue: "8870" },
                { label: "Qdrant HTTP", defaultValue: "6733" },
              ].map((port) => (
                <div key={port.label} className="flex items-center justify-between py-1">
                  <span className="text-sm text-zinc-600 dark:text-zinc-400">{port.label}</span>
                  <input
                    type="number"
                    defaultValue={port.defaultValue}
                    className="w-24 rounded border border-zinc-300 px-2 py-1 text-right text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                  />
                </div>
              ))}
            </SettingsSection>

            <SettingsSection title="Import Settings">
              <p className="mb-2 text-sm text-zinc-600 dark:text-zinc-400">
                Upload a .env.local file to import API keys and configuration.
                Secrets will be stored securely in your Mac Keychain.
              </p>
              <label className="flex cursor-pointer items-center justify-center rounded-lg border-2 border-dashed border-zinc-300 p-6 transition-colors hover:border-zinc-400 dark:border-zinc-700 dark:hover:border-zinc-600">
                <div className="text-center">
                  <p className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
                    Drop .env.local here or click to browse
                  </p>
                  <p className="mt-1 text-xs text-zinc-500">
                    Secrets will be separated and stored in Keychain
                  </p>
                </div>
                <input type="file" className="hidden" accept=".env,.env.local" />
              </label>
            </SettingsSection>
          </>
        )}

        <div className="flex justify-end gap-3 pt-4">
          <button className="rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 dark:border-zinc-600 dark:text-zinc-300">
            Cancel
          </button>
          <button className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white dark:bg-zinc-100 dark:text-zinc-900">
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}

function SettingsSection({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
      <h3 className="mb-3 text-sm font-medium text-zinc-900 dark:text-zinc-100">
        {title}
      </h3>
      {children}
    </div>
  );
}
