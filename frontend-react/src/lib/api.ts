// src/lib/api.ts
import axios from "axios";
import type { OptionsResponse } from "@/types/options";
import type { AnalyzeRequest } from "@/types/request";
import type { AnalyzeResponse } from "@/types/response";

// Vite proxy: /api/* → http://localhost:8000/*
const api = axios.create({
  baseURL: "/api",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 120000, // 2 min — LLM može da bude spor
});

// ───── ENDPOINTS ─────

export async function fetchOptions(): Promise<OptionsResponse> {
  const { data } = await api.get<OptionsResponse>("/options");
  return data;
}

export async function postAnalyze(body: AnalyzeRequest): Promise<AnalyzeResponse> {
  const { data } = await api.post<AnalyzeResponse>("/analyze", body);
  return data;
}

// ───── ERROR HANDLER ─────

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (error.response?.data) {
      const data = error.response.data;
      if (typeof data === "string") return data;
      if (data.detail) {
        if (Array.isArray(data.detail)) {
          return data.detail
            .map((e: { loc?: string[]; msg?: string }) =>
              `${e.loc?.join(".")}: ${e.msg}`
            )
            .join("; ");
        }
        return String(data.detail);
      }
      return JSON.stringify(data);
    }
    return error.message;
  }
  return error instanceof Error ? error.message : "Unknown error";
}

export default api;
