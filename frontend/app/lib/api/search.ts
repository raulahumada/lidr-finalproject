/** Thin client for POST /api/v1/search — types mirrored from backend schemas/search.py */

import { AnswerApiError, getApiBaseUrl } from "./answer";

export type SearchRequest = {
  query: string;
  k?: number;
};

export type SearchHit = {
  chunk_id: number;
  document_id: number;
  chunk_type: string;
  content: string;
  score: number;
  distance: number;
  source_path: string;
  document_type: string;
  metadata: Record<string, unknown>;
};

export type SearchResponse = {
  query: string;
  k: number;
  search_time_ms: number;
  results: SearchHit[];
};

async function readErrorDetail(res: Response): Promise<string> {
  let detail = res.statusText || "Error desconocido";
  try {
    const payload = (await res.json()) as { detail?: unknown };
    if (typeof payload.detail === "string") detail = payload.detail;
  } catch {
    /* ignore body parse */
  }
  return detail;
}

export async function postSearch(body: SearchRequest): Promise<SearchResponse> {
  const url = `${getApiBaseUrl()}/api/v1/search`;
  let res: Response;
  try {
    res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new AnswerApiError(
      "No se pudo conectar con la API. ¿Está corriendo el backend?",
      { kind: "network" },
    );
  }

  if (res.status === 503) {
    throw new AnswerApiError(
      "Servicio no disponible (503). Suele faltar OPENAI_API_KEY en el backend.",
      { status: 503, kind: "unavailable" },
    );
  }

  if (!res.ok) {
    throw new AnswerApiError(
      `Error HTTP ${res.status}: ${await readErrorDetail(res)}`,
      { status: res.status, kind: "http" },
    );
  }

  return (await res.json()) as SearchResponse;
}
