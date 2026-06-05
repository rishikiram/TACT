import { useQuery } from "@tanstack/react-query";
import { fetchAllTrials } from "../api/trials";
import type { FetchTrialsParams } from "../api/trials";

export function useAllTrials(params: FetchTrialsParams) {
  return useQuery({
    queryKey: ["trials/all", params],
    queryFn: () => fetchAllTrials(params),
    enabled: Object.keys(params).length > 0,
  });
}
