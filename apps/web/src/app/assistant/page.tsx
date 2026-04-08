"use client";

import { useEffect, useState } from "react";
import { api, type SearchResult } from "@/lib/api";

const AGENT_ZERO_URL = "http://127.0.0.1:50001";

type ChatMessage =
  | { role: "user"; content: string }
  | { role: "assistant"; content: string; sources: SearchResult[] };

const QUICK_ACTIONS = [
  "Morning Brief",
  "Search my emails",
  "What meetings do I have?",
] as const;

export default function AssistantPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [agentZeroRunning, setAgentZeroRunning] = useState<boolean | null>(null);
  const [detectError, setDetectError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const d = await api.detect.all();
        if (!cancelled) {
          setAgentZeroRunning(d.agent_zero.running);
          setDetectError(null);
        }
      } catch (e) {
        if (!cancelled) {
          setAgentZeroRunning(null);
          setDetectError(e instanceof Error ? e.message : "Could not check Agent Zero");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  async function sendMessage(text: string) {
    const trimmed = text.trim();
    if (!trimmed) return;

    setMessages((prev) => [...prev, { role: "user", content: trimmed }]);

    try {
      const { response, sources } = await api.chat(trimmed);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: response, sources: sources ?? [] },
      ]);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Request failed";
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Something went wrong: ${msg}`, sources: [] },
      ]);
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const text = input;
    setInput("");
    void sendMessage(text);
  }

  return (
    <div className="flex flex-1 flex-col p-8">
      <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">Assistant</h1>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            Chat with local memory search; optional Agent Zero when running
          </p>
        </div>
        <div className="flex flex-col items-start gap-2 sm:items-end">
          {agentZeroRunning === true && (
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-medium text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-200">
                Agent Zero connected
              </span>
              <a
                href={AGENT_ZERO_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm font-medium text-zinc-700 underline-offset-2 hover:underline dark:text-zinc-300"
              >
                Open Agent Zero UI
              </a>
            </div>
          )}
          {agentZeroRunning === false && (
            <p className="max-w-md text-xs text-zinc-500 dark:text-zinc-400">
              Using local memory search. Enable Agent Zero in Settings for smarter conversations.
            </p>
          )}
          {detectError && (
            <p className="max-w-md text-xs text-amber-700 dark:text-amber-300">{detectError}</p>
          )}
        </div>
      </div>

      <div className="flex min-h-[420px] flex-1 flex-col rounded-xl border border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900">
        <div className="flex flex-1 flex-col overflow-y-auto p-4">
          {messages.length === 0 ? (
            <div className="flex flex-1 flex-col items-center justify-center gap-6 p-6 text-center">
              <div>
                <p className="text-4xl" aria-hidden>
                  💬
                </p>
                <h2 className="mt-4 text-lg font-medium text-zinc-700 dark:text-zinc-300">
                  Ask anything about your work
                </h2>
                <p className="mt-2 max-w-md text-sm text-zinc-500 dark:text-zinc-400">
                  Messages use search-backed answers from your indexed data.
                </p>
              </div>
              <div className="flex flex-wrap justify-center gap-2">
                {QUICK_ACTIONS.map((label) => (
                  <button
                    key={label}
                    type="button"
                    onClick={() => void sendMessage(label)}
                    className="rounded-full border border-zinc-300 bg-white px-4 py-2 text-sm font-medium text-zinc-800 transition-colors hover:bg-zinc-100 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-100 dark:hover:bg-zinc-700"
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <ul className="mx-auto flex w-full max-w-3xl flex-col gap-4">
              {messages.map((m, i) => (
                <li
                  key={`${i}-${m.role}-${m.content.slice(0, 24)}`}
                  className={`rounded-xl px-4 py-3 text-sm ${
                    m.role === "user"
                      ? "ml-8 bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                      : "mr-8 border border-zinc-200 bg-white text-zinc-800 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-100"
                  }`}
                >
                  <div className="mb-1 text-xs font-medium uppercase tracking-wide opacity-70">
                    {m.role === "user" ? "You" : "Assistant"}
                  </div>
                  <div className="whitespace-pre-wrap">{m.content}</div>
                  {m.role === "assistant" && m.sources.length > 0 && (
                    <div className="mt-3 border-t border-zinc-200 pt-3 dark:border-zinc-700">
                      <p className="mb-2 text-xs font-medium text-zinc-500 dark:text-zinc-400">
                        Sources
                      </p>
                      <ul className="space-y-2">
                        {m.sources.map((s) => (
                          <li
                            key={`${s.record_id}-${s.title}-${s.score}`}
                            className="rounded-lg bg-zinc-50 px-3 py-2 text-xs dark:bg-zinc-900"
                          >
                            <div className="font-medium text-zinc-800 dark:text-zinc-200">
                              {s.title || s.source || "Untitled"}
                            </div>
                            <div className="mt-0.5 text-zinc-500 dark:text-zinc-400">
                              {s.source}
                              {s.timestamp ? ` · ${s.timestamp}` : ""}
                            </div>
                            {s.snippet && (
                              <p className="mt-1 line-clamp-3 text-zinc-600 dark:text-zinc-300">
                                {s.snippet}
                              </p>
                            )}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>

        <form
          onSubmit={handleSubmit}
          className="border-t border-zinc-200 p-4 dark:border-zinc-800"
        >
          <div className="mx-auto flex max-w-3xl gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask anything about your work…"
              className="flex-1 rounded-lg border border-zinc-300 bg-white px-4 py-2 text-sm text-zinc-900 placeholder:text-zinc-400 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
            />
            <button
              type="submit"
              className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white dark:bg-zinc-100 dark:text-zinc-900"
            >
              Send
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
