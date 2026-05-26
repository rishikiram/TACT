import { useQuery } from "@tanstack/react-query";
import { fetchDbTrials } from "../api/dbTrials";
import type { DbFetchParams } from "../api/dbTrials";

export function useDbTrials(params: DbFetchParams) {
  return useQuery({
    queryKey: ["dbTrials", params],
    queryFn: () => fetchDbTrials(params),
    enabled: Boolean(params.preset || params.condition),
  });
}
