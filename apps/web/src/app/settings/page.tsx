"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";
import { api } from "@/lib/api";

type Mode = "basic" | "advanced";

type SettingsForm = {
  vault_path: string;
  mail_enabled: boolean;
  calendar_enabled: boolean;
  screen_enabled: boolean;
  documents_enabled: boolean;
  vault_enabled: boolean;
  llm_provider: string;
  api_port: number;
  web_dev_port: number;
  mcp_port: number;
  qdrant_http_port: number;
};

type SourceToggleKey =
  | "mail_enabled"
  | "calendar_enabled"
  | "screen_enabled"
  | "documents_enabled"
  | "vault_enabled";

const SOURCE_ROWS: { label: string; key: SourceToggleKey }[] = [
  { label: "Mail", key: "mail_enabled" },
  { label: "Calendar", key: "calendar_enabled" },
  { label: "Screen Capture", key: "screen_enabled" },
  { label: "Documents", key: "documents_enabled" },
  { label: "Obsidian Vault", key: "vault_enabled" },
];

type PortKey = "api_port" | "web_dev_port" | "mcp_port" | "qdrant_http_port";

const PORT_ROWS: { label: string; key: PortKey }[] = [
  { label: "API", key: "api_port" },
  { label: "Web", key: "web_dev_port" },
  { label: "MCP", key: "mcp_port" },
  { label: "Qdrant HTTP", key: "qdrant_http_port" },
];

function defaultForm(): SettingsForm {
  return {
    vault_path: "~/Documents/Praxo-PICOS",
    mail_enabled: true,
    calendar_enabled: true,
    screen_enabled: false,
    documents_enabled: false,
    vault_enabled: false,
    llm_provider: "openai",
    api_port: 8865,
    web_dev_port: 3100,
    mcp_port: 8870,
    qdrant_http_port: 6733,
  };
}

function configToForm(c: Record<string, any>): SettingsForm {
  const d = defaultForm();
  return {
    vault_path: typeof c.vault_path === "string" ? c.vault_path : d.vault_path,
    mail_enabled: typeof c.mail_enabled === "boolean" ? c.mail_enabled : d.mail_enabled,
    calendar_enabled:
      typeof c.calendar_enabled === "boolean" ? c.calendar_enabled : d.calendar_enabled,
    screen_enabled: typeof c.screen_enabled === "boolean" ? c.screen_enabled : d.screen_enabled,
    documents_enabled:
      typeof c.documents_enabled === "boolean" ? c.documents_enabled : d.documents_enabled,
    vault_enabled: typeof c.vault_enabled === "boolean" ? c.vault_enabled : d.vault_enabled,
    llm_provider: typeof c.llm_provider === "string" ? c.llm_provider : d.llm_provider,
    api_port: typeof c.api_port === "number" && Number.isFinite(c.api_port) ? c.api_port : d.api_port,
    web_dev_port:
      typeof c.web_dev_port === "number" && Number.isFinite(c.web_dev_port)
        ? c.web_dev_port
        : d.web_dev_port,
    mcp_port: typeof c.mcp_port === "number" && Number.isFinite(c.mcp_port) ? c.mcp_port : d.mcp_port,
    qdrant_http_port:
      typeof c.qdrant_http_port === "number" && Number.isFinite(c.qdrant_http_port)
        ? c.qdrant_http_port
        : d.qdrant_http_port,
  };
}

function formToSaveBody(f: SettingsForm): Record<string, any> {
  return {
    vault_path: f.vault_path,
    mail_enabled: f.mail_enabled,
    calendar_enabled: f.calendar_enabled,
    screen_enabled: f.screen_enabled,
    documents_enabled: f.documents_enabled,
    vault_enabled: f.vault_enabled,
    llm_provider: f.llm_provider,
    api_port: f.api_port,
    web_dev_port: f.web_dev_port,
    mcp_port: f.mcp_port,
    qdrant_http_port: f.qdrant_http_port,
  };
}

export default function SettingsPage() {
  const [mode, setMode] = useState<Mode>("basic");
  const [testStatus, setTestStatus] = useState<string | null>(null);
  const [form, setForm] = useState<SettingsForm | null>(null);
  const [baseline, setBaseline] = useState<SettingsForm | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saveFeedback, setSaveFeedback] = useState<{ type: "ok" | "err"; text: string } | null>(null);
  const [saving, setSaving] = useState(false);

  const loadConfig = useCallback(async () => {
    setLoadError(null);
    try {
      const { config } = await api.config.get();
      const next = configToForm(config);
      setForm(next);
      setBaseline(next);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Failed to load settings";
      setLoadError(msg);
      const fallback = defaultForm();
      setForm(fallback);
      setBaseline(fallback);
    }
  }, []);

  useEffect(() => {
    loadConfig();
  }, [loadConfig]);

  async function handleTestConnection() {
    setTestStatus("Testing…");
    try {
      const health = await api.health();
      setTestStatus(
        health.status === "ok" ? "Connected — API is healthy" : `API status: ${health.status}`
      );
    } catch {
      setTestStatus("Connection failed");
    }
  }

  async function handleSave() {
    if (!form) return;
    setSaveFeedback(null);
    setSaving(true);
    try {
      await api.config.save(formToSaveBody(form));
      setBaseline(form);
      setSaveFeedback({ type: "ok", text: "Settings saved." });
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Save failed";
      setSaveFeedback({ type: "err", text: msg });
    } finally {
      setSaving(false);
    }
  }

  function handleCancel() {
    if (baseline) setForm(baseline);
    setSaveFeedback(null);
  }

  function updateForm<K extends keyof SettingsForm>(key: K, value: SettingsForm[K]) {
    setForm((prev) => (prev ? { ...prev, [key]: value } : prev));
  }

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
              type="button"
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

      {loadError && (
        <p className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-200">
          Could not load saved config ({loadError}). Showing defaults.
        </p>
      )}

      {!form ? (
        <p className="text-sm text-zinc-500 dark:text-zinc-400">Loading settings…</p>
      ) : (
        <div className="max-w-2xl space-y-6">
          <SettingsSection title="Memory Folder">
            <div className="flex items-center gap-3">
              <input
                type="text"
                value={form.vault_path}
                onChange={(e) => updateForm("vault_path", e.target.value)}
                className="flex-1 rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
              />
              <button
                type="button"
                className="rounded-lg border border-zinc-300 px-3 py-2 text-sm font-medium dark:border-zinc-600 dark:text-zinc-300"
              >
                Browse
              </button>
            </div>
            <p className="mt-1 text-xs text-zinc-500">
              Recommended — Where your memories and summaries are stored
            </p>
          </SettingsSection>

          <SettingsSection title="Data Sources">
            {SOURCE_ROWS.map((row) => (
              <label key={row.key} className="flex items-center justify-between py-2">
                <span className="text-sm text-zinc-700 dark:text-zinc-300">{row.label}</span>
                <input
                  type="checkbox"
                  checked={form[row.key]}
                  onChange={(e) => updateForm(row.key, e.target.checked)}
                  className="h-4 w-4 rounded border-zinc-300 text-zinc-900 dark:border-zinc-600"
                />
              </label>
            ))}
          </SettingsSection>

          <SettingsSection title="AI Provider">
            <select
              value={form.llm_provider}
              onChange={(e) => updateForm("llm_provider", e.target.value)}
              className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
            >
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="openrouter">OpenRouter</option>
            </select>
            <button
              type="button"
              onClick={handleTestConnection}
              className="mt-2 rounded-lg border border-zinc-300 px-3 py-1.5 text-xs font-medium text-zinc-600 dark:border-zinc-600 dark:text-zinc-400"
            >
              Test Connection
            </button>
            {testStatus && (
              <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">{testStatus}</p>
            )}
          </SettingsSection>

          {mode === "advanced" && (
            <>
              <SettingsSection title="Ports">
                {PORT_ROWS.map((port) => (
                  <div key={port.key} className="flex items-center justify-between py-1">
                    <span className="text-sm text-zinc-600 dark:text-zinc-400">{port.label}</span>
                    <input
                      type="number"
                      value={form[port.key] as number}
                      onChange={(e) => {
                        const n = parseInt(e.target.value, 10);
                        updateForm(port.key, Number.isFinite(n) ? n : 0);
                      }}
                      className="w-24 rounded border border-zinc-300 px-2 py-1 text-right text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                    />
                  </div>
                ))}
              </SettingsSection>

              <SettingsSection title="Import Settings">
                <p className="mb-2 text-sm text-zinc-600 dark:text-zinc-400">
                  Upload a .env.local file to import API keys and configuration. Secrets will be stored
                  securely in your Mac Keychain.
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

          {saveFeedback && (
            <p
              className={`text-sm ${
                saveFeedback.type === "ok"
                  ? "text-emerald-600 dark:text-emerald-400"
                  : "text-red-600 dark:text-red-400"
              }`}
              role={saveFeedback.type === "err" ? "alert" : undefined}
            >
              {saveFeedback.text}
            </p>
          )}

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={handleCancel}
              disabled={saving}
              className="rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 disabled:opacity-50 dark:border-zinc-600 dark:text-zinc-300"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={saving}
              className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
            >
              {saving ? "Saving…" : "Save Changes"}
            </button>
          </div>
        </div>
      )}
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
