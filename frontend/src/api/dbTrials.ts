// API client for the FastAPI DB backend (proxied via /db-api)
import type { Trial, FetchTrialsResult } from "./trials";

export interface DbFetchParams {
  preset?: string;
  condition?: string;
  status?: string;
  phases?: string; // comma-separated phase numbers e.g. "2,3"
}

export async function fetchDbPresets(): Promise<string[]> {
  const res = await fetch("/db-api/db/presets");
  if (!res.ok) throw new Error(`Failed to fetch presets: ${res.status}`);
  const data = await res.json();
  return data.presets as string[];
}

export async function fetchDbTrials(params: DbFetchParams): Promise<FetchTrialsResult> {
  const query = new URLSearchParams();
  if (params.preset) query.set("preset", params.preset);
  if (params.condition) query.set("condition", params.condition);
  if (params.status) query.set("status", params.status);
  if (params.phases) query.set("phases", params.phases);

  const res = await fetch(`/db-api/db/trials?${query.toString()}`);
  if (!res.ok) throw new Error(`Failed to fetch trials: ${res.status}`);
  const data = await res.json();
  return { trials: data.trials as Trial[] };
}
