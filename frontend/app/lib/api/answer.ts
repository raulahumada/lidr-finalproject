/** Thin client for POST /api/v1/answer — types mirrored from backend schemas/answer.py */

export type AnswerRequest = {
  question: string;
  k?: number;
};

export type Citation = {
  chunk_id: number;
  document_id: number;
  source_path: string;
  document_type: string;
  score: number;
  excerpt: string;
  metadata: Record<string, unknown>;
};

export type AnswerResponse = {
  question: string;
  answer: string;
  citations: Citation[];
  cached: "exact" | "semantic" | "false";
  prompt_version: string;
  k: number;
  latency_ms: number;
  no_evidence: boolean;
};

export class AnswerApiError extends Error {
  readonly status: number | null;
  readonly kind: "unavailable" | "http" | "network";

  constructor(
    message: string,
    opts: { status?: number | null; kind: AnswerApiError["kind"] },
  ) {
    super(message);
    this.name = "AnswerApiError";
    this.status = opts.status ?? null;
    this.kind = opts.kind;
  }
}

/**
 * Browser clients call the same-origin BFF (`/api/v1/...`).
 * The BFF attaches SERVICE_TOKEN server-side — never use NEXT_PUBLIC_ for that secret.
 */
export function getApiBaseUrl(): string {
  return "";
}

export async function postAnswer(
  body: AnswerRequest,
): Promise<AnswerResponse> {
  const url = `${getApiBaseUrl()}/api/v1/answer`;
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
    let detail = res.statusText || "Error desconocido";
    try {
      const payload = (await res.json()) as { detail?: unknown };
      if (typeof payload.detail === "string") detail = payload.detail;
    } catch {
      /* ignore body parse */
    }
    throw new AnswerApiError(`Error HTTP ${res.status}: ${detail}`, {
      status: res.status,
      kind: "http",
    });
  }

  return (await res.json()) as AnswerResponse;
}
