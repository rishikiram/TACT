import type { QueryResult } from "./cache";

export const CT_GOV_BASE = "https://clinicaltrials.gov/api/v2/studies";
const PAGE_CAP = 20; // max 20,000 studies per request

export async function fetchAllPages(baseParams: URLSearchParams): Promise<QueryResult> {
  baseParams.set("pageSize", "1000");
  baseParams.delete("pageToken");

  const allStudies: unknown[] = [];
  let pageToken: string | undefined;
  let page = 0;

  do {
    page++;
    const params = new URLSearchParams(baseParams);
    if (pageToken) params.set("pageToken", pageToken);

    const url = `${CT_GOV_BASE}?${params.toString()}`;
    console.log(`[/api/trials/all] page ${page} — ${url}`);

    const response = await fetch(url, { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error(`CT.gov returned ${response.status}`);

    const data = await response.json() as { studies?: unknown[]; nextPageToken?: string };
    allStudies.push(...(data.studies ?? []));
    pageToken = data.nextPageToken;

    console.log(
      `[/api/trials/all] page ${page}: ${(data.studies ?? []).length} studies (running total: ${allStudies.length})`
    );
  } while (pageToken && page < PAGE_CAP);

  if (pageToken && page >= PAGE_CAP) {
    console.warn(`[/api/trials/all] hit ${PAGE_CAP}-page cap — results may be incomplete`);
  }

  return { studies: allStudies, totalCount: allStudies.length };
}
