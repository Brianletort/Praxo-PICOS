async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export interface HealthResponse {
  status: "ok" | "degraded" | "error";
  service: string;
  uptime_seconds: number;
  dependencies: Record<string, { status: string; latency_ms?: number; error?: string }>;
}

export interface SearchResult {
  record_id: string;
  title: string;
  snippet: string;
  source: string;
  timestamp: string;
  score: number;
  match_type: string;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total: number;
}

export interface SourceStatus {
  name: string;
  enabled: boolean;
  status: string;
  last_extraction?: string;
  records_count?: number;
}

export interface DataFlowEntry {
  source: string;
  status: string;
  last_record_at: string | null;
  records_synced: number;
  error_message: string | null;
}

export const api = {
  health: () => apiFetch<HealthResponse>("/_api/health"),
  readiness: () => apiFetch<{ status: string }>("/_api/health/ready"),
  search: (query: string, limit = 10) =>
    apiFetch<SearchResponse>(`/api/search?q=${encodeURIComponent(query)}&limit=${limit}`),
  sources: {
    list: () => apiFetch<{ sources: SourceStatus[] }>("/api/sources"),
    status: (name: string) => apiFetch<SourceStatus>(`/api/sources/${name}`),
  },
  dataFlow: () => apiFetch<{ data_flow: DataFlowEntry[] }>("/api/data-flow"),
  config: {
    get: () => apiFetch<{ config: Record<string, any> }>("/api/config"),
    save: (config: Record<string, any>) =>
      apiFetch<{ status: string }>("/api/config", {
        method: "POST",
        body: JSON.stringify(config),
      }),
    patch: (updates: Record<string, any>) =>
      apiFetch<{ status: string }>("/api/config", {
        method: "PATCH",
        body: JSON.stringify(updates),
      }),
  },
  extract: {
    run: () =>
      apiFetch<{ status: string; result?: any; error?: string }>("/api/extract/run", {
        method: "POST",
      }),
  },
};
