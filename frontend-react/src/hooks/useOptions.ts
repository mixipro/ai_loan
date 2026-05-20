// src/hooks/useOptions.ts
import { useQuery } from "@tanstack/react-query";
import { fetchOptions } from "@/lib/api";

export function useOptions() {
  return useQuery({
    queryKey: ["options"],
    queryFn: fetchOptions,
    staleTime: 1000 * 60 * 60, // 1h cache
  });
}
