/** Thin client for /api/v1/ingest — types mirrored from backend schemas/ingest.py */

import { AnswerApiError, getApiBaseUrl } from "./answer";

export type IngestRunStatus = "queued" | "running" | "completed" | "failed";

export type IngestSummary = {
  seen: number;
  ingested: number;
  skipped_extension: number;
  skipped_existing: number;
  failed: number;
  chunks: number;
  errors: string[];
};

export type IngestStats = {
  document_count: number;
  chunk_count: number;
  corpus_root: string;
  allowlist: string[];
};

export type IngestRunStart = {
  run_id: string;
  status: "queued" | "running";
};

export type IngestRunView = {
  run_id: string;
  status: IngestRunStatus;
  force: boolean;
  summary: IngestSummary | null;
  error: string | null;
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

function raiseForStatus(res: Response, detail: string): never {
  if (res.status === 503) {
    throw new AnswerApiError(
      detail ||
        "Servicio no disponible (503). Revisá CORPUS_ROOT, OPENAI_API_KEY y DATABASE_URL.",
      { status: 503, kind: "unavailable" },
    );
  }
  if (res.status === 409) {
    throw new AnswerApiError(
      detail || "Ya hay una ingesta en curso. Esperá a que termine.",
      { status: 409, kind: "http" },
    );
  }
  throw new AnswerApiError(`Error HTTP ${res.status}: ${detail}`, {
    status: res.status,
    kind: "http",
  });
}

export async function getIngestStats(): Promise<IngestStats> {
  const url = `${getApiBaseUrl()}/api/v1/ingest/stats`;
  let res: Response;
  try {
    res = await fetch(url);
  } catch {
    throw new AnswerApiError(
      "No se pudo conectar con la API. ¿Está corriendo el backend?",
      { kind: "network" },
    );
  }
  if (!res.ok) {
    raiseForStatus(res, await readErrorDetail(res));
  }
  return (await res.json()) as IngestStats;
}

export async function startIngestRun(force = false): Promise<IngestRunStart> {
  const url = `${getApiBaseUrl()}/api/v1/ingest/runs`;
  let res: Response;
  try {
    res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ force }),
    });
  } catch {
    throw new AnswerApiError(
      "No se pudo conectar con la API. ¿Está corriendo el backend?",
      { kind: "network" },
    );
  }
  if (!res.ok) {
    raiseForStatus(res, await readErrorDetail(res));
  }
  return (await res.json()) as IngestRunStart;
}

export async function getIngestRun(runId: string): Promise<IngestRunView> {
  const url = `${getApiBaseUrl()}/api/v1/ingest/runs/${encodeURIComponent(runId)}`;
  let res: Response;
  try {
    res = await fetch(url);
  } catch {
    throw new AnswerApiError(
      "No se pudo conectar con la API. ¿Está corriendo el backend?",
      { kind: "network" },
    );
  }
  if (!res.ok) {
    raiseForStatus(res, await readErrorDetail(res));
  }
  return (await res.json()) as IngestRunView;
}

const TERMINAL: ReadonlySet<IngestRunStatus> = new Set(["completed", "failed"]);

export async function runIngestWithProgress(
  force: boolean,
  onUpdate: (view: IngestRunView) => void,
  options?: { pollMs?: number; signal?: AbortSignal },
): Promise<IngestRunView> {
  const pollMs = options?.pollMs ?? 1200;
  const started = await startIngestRun(force);
  let view: IngestRunView = {
    run_id: started.run_id,
    status: started.status,
    force,
    summary: null,
    error: null,
  };
  onUpdate(view);

  while (!TERMINAL.has(view.status)) {
    if (options?.signal?.aborted) {
      throw new AnswerApiError("Ingesta cancelada en el cliente.", {
        kind: "http",
      });
    }
    await new Promise((r) => setTimeout(r, pollMs));
    view = await getIngestRun(started.run_id);
    onUpdate(view);
  }
  return view;
}
