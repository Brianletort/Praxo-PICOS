"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, type DetectAllResponse, type HealthResponse } from "@/lib/api";

const FALLBACK_MEMORY_FOLDER = "~/Documents/Praxo-PICOS";

const STEPS = [
  {
    title: "Where should we keep your memories?",
    description:
      "Pick one folder on your computer. We will save your daily notes and summaries there so you can find them easily.",
  },
  {
    title: "What should we learn from?",
    description:
      "Turn on the feeds you want. We only use what you allow. If we spot something already working on your computer, we show a small “Detected” tag.",
  },
  {
    title: "Which thinking helper do you want?",
    description:
      "This picks who powers the smart replies. You can add your account key later in Settings.",
  },
  {
    title: "Is the helper app awake?",
    description:
      "We check that the small program on your computer answered us. If it did, you are ready for the next step.",
  },
  {
    title: "Extra smart worker (optional)",
    description:
      "This is an add-on that can search your memories and do bigger jobs. It needs a common tool called Docker if you want it on.",
  },
];

type SourcesState = {
  mail: boolean;
  calendar: boolean;
  screen: boolean;
  documents: boolean;
  vault: boolean;
};

function badgeSuggested() {
  return (
    <span className="ml-2 inline-flex items-center rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300">
      Suggested
    </span>
  );
}

function badgeRecommended() {
  return (
    <span className="ml-2 inline-flex items-center rounded-full bg-sky-100 px-2 py-0.5 text-xs font-medium text-sky-800 dark:bg-sky-900/40 dark:text-sky-300">
      Recommended
    </span>
  );
}

function badgeDetected() {
  return (
    <span className="ml-2 inline-flex items-center rounded-full bg-violet-100 px-2 py-0.5 text-xs font-medium text-violet-800 dark:bg-violet-900/40 dark:text-violet-300">
      Detected
    </span>
  );
}

function onboardingToSaveBody(
  vaultPath: string,
  sources: SourcesState,
  provider: string,
  agentZero: boolean,
  documentsPath: string,
): Record<string, unknown> {
  const body: Record<string, unknown> = {
    vault_path: vaultPath,
    mail_enabled: sources.mail,
    calendar_enabled: sources.calendar,
    screen_enabled: sources.screen,
    documents_enabled: sources.documents,
    vault_enabled: sources.vault,
    llm_provider: provider,
    agent_zero_enabled: agentZero,
  };
  if (sources.documents && documentsPath.trim()) {
    body.documents_path = documentsPath.trim();
  }
  return body;
}

type SaveConfigResult =
  | { status: "saved"; keys?: string[] }
  | { status: "updated"; keys?: string[] }
  | { status: "validation_error"; errors: string[] };

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [detect, setDetect] = useState<DetectAllResponse | null>(null);
  const [detectError, setDetectError] = useState<string | null>(null);
  const [vaultPath, setVaultPath] = useState("");
  const [sources, setSources] = useState<SourcesState>({
    mail: true,
    calendar: true,
    screen: false,
    documents: false,
    vault: false,
  });
  const [provider, setProvider] = useState("openai");
  const [agentZero, setAgentZero] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);
  const [finishing, setFinishing] = useState(false);
  const [finishError, setFinishError] = useState<string | null>(null);

  const suggestedVaultPath =
    detect?.suggestions.vault_path?.trim() ||
    (detect?.obsidian.found && detect.obsidian.vaults[0]?.path) ||
    FALLBACK_MEMORY_FOLDER;
  const suggestedDocumentsPath =
    detect?.suggestions.documents_path?.trim() || detect?.documents.path?.trim() || "";

  const pathIsSuggested =
    vaultPath.trim() === suggestedVaultPath.trim() ||
    (detect?.obsidian.vaults.some((v) => v.path.trim() === vaultPath.trim()) ?? false);

  async function refreshHealth() {
    setHealthLoading(true);
    setHealthError(null);
    try {
      const h = await api.health();
      setHealth(h);
    } catch (e) {
      setHealth(null);
      setHealthError(e instanceof Error ? e.message : "No answer from the helper app.");
    } finally {
      setHealthLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setDetectError(null);
      try {
        const d = await api.detect.all();
        if (cancelled) return;
        setDetect(d);

        const firstVault = d.obsidian.found && d.obsidian.vaults[0]?.path;
        const initialVault =
          firstVault || d.suggestions.vault_path?.trim() || FALLBACK_MEMORY_FOLDER;
        setVaultPath(initialVault);

        setSources({
          mail: true,
          calendar: true,
          screen: d.screenpipe.running,
          documents: d.documents.exists,
          vault: d.obsidian.found,
        });

        setAgentZero(d.agent_zero.running);
      } catch (e) {
        if (!cancelled) {
          setDetectError(
            e instanceof Error
              ? e.message
              : "We could not scan your computer. You can still type paths by hand.",
          );
          setVaultPath(FALLBACK_MEMORY_FOLDER);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    refreshHealth();
  }, []);

  const currentStep = STEPS[step];
  const isFirst = step === 0;
  const isLast = step === STEPS.length - 1;

  const helperAppReachable = health !== null && !healthError;
  const helperAppHappy = helperAppReachable && health?.status === "ok";

  async function handleNextOrFinish() {
    if (!isLast) {
      setStep(step + 1);
      return;
    }
    setFinishError(null);
    setFinishing(true);
    try {
      const body = onboardingToSaveBody(
        vaultPath,
        sources,
        provider,
        agentZero,
        suggestedDocumentsPath,
      );
      const result = (await api.config.save(body)) as SaveConfigResult;
      if (result.status === "validation_error") {
        setFinishError(result.errors?.join(" ") ?? "Something in your choices did not work. Try again.");
        return;
      }
      if (result.status !== "saved" && result.status !== "updated") {
        setFinishError("Could not save your choices. Try again.");
        return;
      }
      localStorage.setItem("picos-onboarding-complete", "true");
      router.push("/");
    } catch (e) {
      setFinishError(e instanceof Error ? e.message : "Could not save your choices.");
    } finally {
      setFinishing(false);
    }
  }

  function setSource<K extends keyof SourcesState>(key: K, value: boolean) {
    setSources((s) => ({ ...s, [key]: value }));
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-white p-8 dark:bg-zinc-950">
      <div className="w-full max-w-lg">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-semibold text-zinc-900 dark:text-zinc-100">
            Welcome to Praxo-PICOS
          </h1>
          <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
            A short setup so the app fits your computer and your habits.
          </p>
        </div>

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

        <div className="mb-8 rounded-xl border border-zinc-200 p-6 dark:border-zinc-800">
          <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-100">
            {currentStep.title}
          </h2>
          <p className="mt-1 mb-6 text-sm text-zinc-500 dark:text-zinc-400">
            {currentStep.description}
          </p>

          {step === 0 && (
            <div className="space-y-4">
              {detectError && (
                <p className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-900 dark:bg-amber-950/40 dark:text-amber-200">
                  {detectError}
                </p>
              )}
              <div>
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
                  Your memory folder
                  {pathIsSuggested ? badgeSuggested() : null}
                </label>
                {detect && detect.obsidian.vaults.length > 0 ? (
                  <div className="mt-2 space-y-2">
                    <p className="text-xs text-zinc-500 dark:text-zinc-400">
                      We found note folders on this machine. Pick one or type a different path below.
                    </p>
                    <select
                      value={
                        detect.obsidian.vaults.some((v) => v.path === vaultPath)
                          ? vaultPath
                          : ""
                      }
                      onChange={(e) => {
                        const v = e.target.value;
                        if (v) setVaultPath(v);
                      }}
                      className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                    >
                      <option value="">Choose a found folder…</option>
                      {detect.obsidian.vaults.map((v) => (
                        <option key={v.path} value={v.path}>
                          {v.name} ({v.note_count} notes)
                        </option>
                      ))}
                    </select>
                  </div>
                ) : null}
                <input
                  type="text"
                  value={vaultPath}
                  onChange={(e) => setVaultPath(e.target.value)}
                  placeholder={FALLBACK_MEMORY_FOLDER}
                  className="mt-2 w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                />
                <p className="mt-2 text-xs text-zinc-600 dark:text-zinc-400">
                  {!detect?.obsidian.found && (
                    <>
                      We did not find a notes app folder, so we suggest{" "}
                      <span className="font-medium">{FALLBACK_MEMORY_FOLDER}</span>{" "}
                      {badgeRecommended()}
                    </>
                  )}
                  {detect?.obsidian.found && (
                    <>
                      Using a folder we found is usually easiest and keeps backups simple.{" "}
                      {badgeRecommended()}
                    </>
                  )}
                </p>
              </div>
            </div>
          )}

          {step === 1 && (
            <div className="space-y-3">
              <SourceRow
                title="Email"
                description="Lets us read patterns from your messages when you turn on mail sync later."
                checked={sources.mail}
                onChange={(v) => setSource("mail", v)}
                recommended
              />
              <SourceRow
                title="Calendar"
                description="Helps us know when you are busy or free when you connect a calendar later."
                checked={sources.calendar}
                onChange={(v) => setSource("calendar", v)}
                recommended
              />
              <SourceRow
                title="Screen and sound"
                description="Remembers what you saw and heard on this computer while the recorder is running."
                checked={sources.screen}
                onChange={(v) => setSource("screen", v)}
                detected={detect?.screenpipe.running}
                detectedLabel={detect?.screenpipe.installed ? "Recorder is running" : undefined}
              />
              <SourceRow
                title="Files in your Documents area"
                description="Adds common files from your usual documents spot so searches feel complete."
                checked={sources.documents}
                onChange={(v) => setSource("documents", v)}
                detected={detect?.documents.exists}
                detectedLabel={detect?.documents.exists ? "Folder is there" : undefined}
              />
              <SourceRow
                title="Notes folder sync"
                description="Keeps the app aligned with the note folders we found on this machine."
                checked={sources.vault}
                onChange={(v) => setSource("vault", v)}
                detected={detect?.obsidian.found}
                detectedLabel={detect?.obsidian.found ? "Note folders found" : undefined}
              />
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
                Thinking helper
              </label>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
              >
                <option value="openai">OpenAI — popular, strong everyday answers (good default)</option>
                <option value="anthropic">Anthropic — careful, great for long writing tasks</option>
                <option value="openrouter">OpenRouter — one sign-in, many models behind it</option>
                <option value="ollama">Ollama — runs on your machine only, private and offline-friendly</option>
                <option value="gemini">Gemini — Google’s helper, good with mixed media questions</option>
              </select>
              <ul className="space-y-2 text-xs text-zinc-600 dark:text-zinc-400">
                <li>
                  <span className="font-medium text-zinc-800 dark:text-zinc-200">OpenAI</span>{" "}
                  {badgeRecommended()} — Like a very well-read assistant many apps already use.
                </li>
                <li>
                  <span className="font-medium text-zinc-800 dark:text-zinc-200">Anthropic</span> — Often
                  feels steady and polite on tricky questions.
                </li>
                <li>
                  <span className="font-medium text-zinc-800 dark:text-zinc-200">OpenRouter</span> — One
                  door to many helpers; handy if you like to switch styles.
                </li>
                <li>
                  <span className="font-medium text-zinc-800 dark:text-zinc-200">Ollama</span> — Stays on
                  your computer; slower device needed, nothing leaves home.
                </li>
                <li>
                  <span className="font-medium text-zinc-800 dark:text-zinc-200">Gemini</span> — Good when
                  you already live in Google’s world.
                </li>
              </ul>
              <p className="text-xs text-zinc-500">
                You will add your own access key in Settings when you are ready. Nothing is sent until you do.
              </p>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4 py-2">
              <div className="flex flex-col items-center gap-3 text-center">
                {healthLoading ? (
                  <p className="text-sm text-zinc-600 dark:text-zinc-400">Checking…</p>
                ) : helperAppHappy ? (
                  <>
                    <span className="text-4xl" aria-hidden>
                      ✓
                    </span>
                    <p className="text-sm font-medium text-emerald-700 dark:text-emerald-400">
                      The helper app answered. You are connected.
                    </p>
                  </>
                ) : helperAppReachable ? (
                  <>
                    <span className="text-4xl text-amber-500" aria-hidden>
                      !
                    </span>
                    <p className="text-sm text-amber-800 dark:text-amber-200">
                      The helper app answered but says it is not fully healthy. You can still continue and
                      fix details later.
                    </p>
                  </>
                ) : (
                  <>
                    <span className="text-4xl text-zinc-400" aria-hidden>
                      ✕
                    </span>
                    <p className="text-sm text-red-600 dark:text-red-400">
                      {healthError ?? "We could not reach the helper app."}
                    </p>
                    <p className="text-xs text-zinc-500">
                      Start the small program that ships with this project, then tap check again.
                    </p>
                  </>
                )}
                <button
                  type="button"
                  onClick={() => refreshHealth()}
                  className="rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 dark:border-zinc-600 dark:text-zinc-300"
                >
                  Check again
                </button>
              </div>
            </div>
          )}

          {step === 4 && (
            <div className="space-y-4">
              {detect && (
                <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-sm dark:border-zinc-800 dark:bg-zinc-900/50">
                  <p className="font-medium text-zinc-800 dark:text-zinc-200">What we noticed</p>
                  <ul className="mt-2 list-inside list-disc space-y-1 text-xs text-zinc-600 dark:text-zinc-400">
                    <li>
                      Box runner (Docker):{" "}
                      {detect.docker.installed
                        ? detect.docker.running
                          ? "Installed and running"
                          : "Installed but not running"
                        : "Not installed on this computer"}
                    </li>
                    <li>
                      Extra worker: {detect.agent_zero.running ? "Already running" : "Not running right now"}
                    </li>
                  </ul>
                </div>
              )}

              {!detect?.docker.installed ? (
                <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-100">
                  <p className="font-medium">Install the “box runner” first</p>
                  <p className="mt-2 text-xs leading-relaxed">
                    The extra smart worker needs a free tool called Docker. Think of Docker as a lunchbox
                    that holds another program safely. Download Docker Desktop for your Mac or Windows,
                    open it once so it runs in the background, then come back here.
                  </p>
                </div>
              ) : (
                <label className="flex items-start justify-between gap-4 rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
                  <div>
                    <span className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
                      Turn on the extra smart worker
                    </span>
                    <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
                      Uses the box runner (Docker) to do deeper searches and jobs. Turn it off anytime.
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={agentZero}
                    onChange={(e) => setAgentZero(e.target.checked)}
                    className="mt-1 h-4 w-4 shrink-0 rounded border-zinc-300 dark:border-zinc-600"
                  />
                </label>
              )}
            </div>
          )}
        </div>

        <div className="space-y-3">
          {finishError && (
            <p className="text-center text-sm text-red-600 dark:text-red-400" role="alert">
              {finishError}
            </p>
          )}
          <div className="flex justify-between">
            <button
              type="button"
              onClick={() => setStep(step - 1)}
              disabled={isFirst}
              className="rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 disabled:opacity-30 dark:border-zinc-600 dark:text-zinc-300"
            >
              Back
            </button>
            <button
              type="button"
              onClick={handleNextOrFinish}
              disabled={finishing}
              className="rounded-lg bg-zinc-900 px-6 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
            >
              {isLast ? (finishing ? "Saving…" : "Finish Setup") : "Next"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function SourceRow(props: {
  title: string;
  description: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  detected?: boolean;
  detectedLabel?: string;
  recommended?: boolean;
}) {
  const { title, description, checked, onChange, detected, detectedLabel, recommended } = props;
  return (
    <label className="flex items-start justify-between gap-3 rounded-lg border border-zinc-200 p-3 dark:border-zinc-800">
      <div className="min-w-0">
        <span className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
          {title}
          {recommended ? badgeRecommended() : null}
          {detected ? badgeDetected() : null}
        </span>
        {detected && detectedLabel ? (
          <p className="text-xs text-emerald-700 dark:text-emerald-400">{detectedLabel}</p>
        ) : null}
        <p className="text-xs text-zinc-500 dark:text-zinc-400">{description}</p>
      </div>
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="mt-1 h-4 w-4 shrink-0 rounded border-zinc-300 dark:border-zinc-600"
      />
    </label>
  );
}
