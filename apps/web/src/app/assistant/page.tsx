export default function AssistantPage() {
  return (
    <div className="flex flex-1 flex-col p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
          Assistant
        </h1>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
          Chat with your personal intelligence system
        </p>
      </div>

      <div className="flex flex-1 flex-col rounded-xl border border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900">
        <div className="flex flex-1 items-center justify-center p-8">
          <div className="text-center">
            <p className="text-4xl">💬</p>
            <h2 className="mt-4 text-lg font-medium text-zinc-700 dark:text-zinc-300">
              Agent Zero will appear here
            </h2>
            <p className="mt-2 max-w-md text-sm text-zinc-500 dark:text-zinc-400">
              Once configured, you can chat with your AI assistant. It has access to
              all your memories, emails, calendar, and documents through the MCP connection.
            </p>
            <a
              href="/settings"
              className="mt-4 inline-block rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
            >
              Configure Agent Zero
            </a>
          </div>
        </div>

        <div className="border-t border-zinc-200 p-4 dark:border-zinc-800">
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Ask anything about your work..."
              disabled
              className="flex-1 rounded-lg border border-zinc-300 bg-white px-4 py-2 text-sm text-zinc-900 placeholder:text-zinc-400 disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
            />
            <button
              disabled
              className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
