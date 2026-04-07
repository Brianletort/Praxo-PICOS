"use client";

import { useState } from "react";

const STEPS = [
  { title: "Pick your Memory Folder", description: "Where should we store your daily summaries and notes?" },
  { title: "Choose what to remember", description: "Select which data sources to connect" },
  { title: "Connect your AI provider", description: "Choose which AI service powers your assistant" },
  { title: "Start background services", description: "Let PICOS work quietly in the background" },
  { title: "Connect Agent Zero", description: "Add an AI assistant that can search your memories" },
];

export default function OnboardingPage() {
  const [step, setStep] = useState(0);
  const [config, setConfig] = useState({
    vaultPath: "",
    sources: { mail: true, calendar: true, screen: false, documents: false, vault: false },
    provider: "openai",
    agentZero: false,
  });

  const currentStep = STEPS[step];
  const isFirst = step === 0;
  const isLast = step === STEPS.length - 1;

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-white p-8 dark:bg-zinc-950">
      <div className="w-full max-w-lg">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-semibold text-zinc-900 dark:text-zinc-100">
            Welcome to Praxo-PICOS
          </h1>
          <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
            Let&apos;s set up your personal intelligence system
          </p>
        </div>

        {/* Progress */}
        <div className="mb-8 flex justify-center gap-2">
          {STEPS.map((_, i) => (
            <div
              key={i}
              className={`h-1.5 w-12 rounded-full transition-colors ${
                i <= step ? "bg-zinc-900 dark:bg-zinc-100" : "bg-zinc-200 dark:bg-zinc-800"
              }`}
            />
          ))}
        </div>

        {/* Step content */}
        <div className="mb-8 rounded-xl border border-zinc-200 p-6 dark:border-zinc-800">
          <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-100">
            {currentStep.title}
          </h2>
          <p className="mt-1 mb-6 text-sm text-zinc-500 dark:text-zinc-400">
            {currentStep.description}
          </p>

          {step === 0 && (
            <div>
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
                Memory folder path
              </label>
              <div className="mt-1 flex gap-2">
                <input
                  type="text"
                  value={config.vaultPath}
                  onChange={(e) => setConfig({ ...config, vaultPath: e.target.value })}
                  placeholder="~/Documents/Praxo-PICOS"
                  className="flex-1 rounded-lg border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                />
                <button className="rounded-lg border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:text-zinc-300">
                  Browse
                </button>
              </div>
              <p className="mt-2 text-xs text-emerald-600 dark:text-emerald-400">
                Recommended — Easy to find, easy to back up
              </p>
            </div>
          )}

          {step === 1 && (
            <div className="space-y-3">
              {Object.entries(config.sources).map(([key, enabled]) => (
                <label key={key} className="flex items-center justify-between rounded-lg border border-zinc-200 p-3 dark:border-zinc-800">
                  <div>
                    <span className="text-sm font-medium capitalize text-zinc-900 dark:text-zinc-100">{key}</span>
                    <p className="text-xs text-zinc-500">
                      {key === "mail" && "Read your email to build context"}
                      {key === "calendar" && "Know your schedule and meetings"}
                      {key === "screen" && "Capture what you see and hear (requires Screenpipe)"}
                      {key === "documents" && "Index files in your Documents folder"}
                      {key === "vault" && "Sync with your Obsidian vault"}
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={enabled}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        sources: { ...config.sources, [key]: e.target.checked },
                      })
                    }
                    className="h-4 w-4 rounded border-zinc-300 dark:border-zinc-600"
                  />
                </label>
              ))}
            </div>
          )}

          {step === 2 && (
            <div>
              <select
                value={config.provider}
                onChange={(e) => setConfig({ ...config, provider: e.target.value })}
                className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
              >
                <option value="openai">OpenAI (GPT-4o)</option>
                <option value="anthropic">Anthropic (Claude)</option>
                <option value="openrouter">OpenRouter (multiple models)</option>
              </select>
              <p className="mt-2 text-xs text-zinc-500">
                You&apos;ll need an API key from your provider. You can add it in Settings later.
              </p>
            </div>
          )}

          {step === 3 && (
            <div className="text-center py-4">
              <p className="text-4xl mb-4">🚀</p>
              <p className="text-sm text-zinc-700 dark:text-zinc-300">
                PICOS will run quietly in the background, keeping your memories up to date.
                You can check on it anytime from the Health page.
              </p>
              <button className="mt-4 rounded-lg bg-emerald-600 px-6 py-2 text-sm font-medium text-white hover:bg-emerald-700">
                Start Services
              </button>
            </div>
          )}

          {step === 4 && (
            <div>
              <label className="flex items-center justify-between rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
                <div>
                  <span className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
                    Enable Agent Zero
                  </span>
                  <p className="text-xs text-zinc-500 mt-1">
                    An AI assistant that can search your memories, write briefs,
                    and answer questions about your work. Requires Docker.
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={config.agentZero}
                  onChange={(e) => setConfig({ ...config, agentZero: e.target.checked })}
                  className="h-4 w-4 rounded border-zinc-300 dark:border-zinc-600"
                />
              </label>
            </div>
          )}
        </div>

        {/* Navigation */}
        <div className="flex justify-between">
          <button
            onClick={() => setStep(step - 1)}
            disabled={isFirst}
            className="rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 disabled:opacity-30 dark:border-zinc-600 dark:text-zinc-300"
          >
            Back
          </button>
          <button
            onClick={() => (isLast ? (window.location.href = "/") : setStep(step + 1))}
            className="rounded-lg bg-zinc-900 px-6 py-2 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
          >
            {isLast ? "Finish Setup" : "Next"}
          </button>
        </div>
      </div>
    </div>
  );
}
