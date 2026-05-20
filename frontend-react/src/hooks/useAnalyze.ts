// src/hooks/useAnalyze.ts
import { useMutation } from "@tanstack/react-query";
import { postAnalyze, getErrorMessage } from "@/lib/api";
import { toast } from "sonner";
import type { AnalyzeRequest } from "@/types/request";
import type { AnalyzeResponse } from "@/types/response";

export function useAnalyze() {
  return useMutation<AnalyzeResponse, Error, AnalyzeRequest>({
    mutationFn: postAnalyze,
    onError: (error) => {
      const msg = getErrorMessage(error);
      console.error("[useAnalyze] error:", msg);
      toast.error("Analysis failed", { description: msg });
    },
    onSuccess: (data) => {
      const count = data.strategies?.length ?? 0;
      toast.success("Analysis complete", {
        description: `Generated ${count} investment strategies.`,
      });
    },
  });
}
