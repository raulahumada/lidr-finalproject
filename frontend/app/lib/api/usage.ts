/**
 * Client for GET /api/v1/usage/summary via the same-origin BFF.
 */

import { AnswerApiError, getApiBaseUrl } from "./answer";

export type UsageByModel = {
  model: string;
  calls: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
};

export type UsageSummary = {
  total_calls: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  by_model: UsageByModel[];
};

export type UsagePurpose =
  | ""
  | "answer"
  | "grounded_composer"
  | "prompt_specialist";

export type UsageFilters = {
  from?: string;
  to?: string;
  sessionId?: string;
  purpose?: UsagePurpose;
};

export async function getUsageSummary(
  filters: UsageFilters = {},
): Promise<UsageSummary> {
  const params = new URLSearchParams();
  if (filters.from) params.set("from", filters.from);
  if (filters.to) params.set("to", filters.to);
  if (filters.sessionId?.trim()) {
    params.set("session_id", filters.sessionId.trim());
  }
  if (filters.purpose) params.set("purpose", filters.purpose);
  const suffix = params.size > 0 ? `?${params}` : "";
  const url = `${getApiBaseUrl()}/api/v1/usage/summary${suffix}`;
  let response: Response;
  try {
    response = await fetch(url, { method: "GET", cache: "no-store" });
  } catch {
    throw new AnswerApiError("No se pudo leer el uso de tokens.", {
      kind: "network",
    });
  }
  const body = (await response.json().catch(() => ({}))) as UsageSummary & {
    error?: string;
    detail?: string | { msg?: string }[];
  };
  if (!response.ok) {
    const detail =
      typeof body.detail === "string"
        ? body.detail
        : body.error || "No se pudo leer el uso de tokens.";
    throw new AnswerApiError(detail, {
      status: response.status,
      kind: "http",
    });
  }
  return body;
}
