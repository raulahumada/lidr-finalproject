/** Thin client for conversation sessions — types mirrored from backend schemas */

import { AnswerApiError, getApiBaseUrl } from "./answer";

export type SessionCreated = {
  session_id: string;
};

export type SessionSummary = {
  session_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  turn_count: number;
};

export type HistoryTurnCitation = {
  chunk_id: number | null;
  document_id: number | null;
  source_path: string;
  document_type: string;
  score: number;
  excerpt: string;
};

export type HistoryTurn = {
  question: string;
  answer: string | null;
  citations: HistoryTurnCitation[];
  status: "completed" | "rejected";
  thread_id: string | null;
  created_at: string;
};

export type SessionView = {
  session_id: string;
  title: string | null;
  history: HistoryTurn[];
  created_at: string;
  updated_at: string;
  turn_count: number;
};

async function readErrorDetail(res: Response): Promise<string> {
  let detail = res.statusText || "Error desconocido";
  try {
    const payload = (await res.json()) as { detail?: unknown };
    if (typeof payload.detail === "string") detail = payload.detail;
  } catch {
    /* ignore */
  }
  return detail;
}

function throwForFailedResponse(res: Response, detail: string): never {
  if (res.status === 404) {
    throw new AnswerApiError("Sesión desconocida o eliminada (404).", {
      status: 404,
      kind: "http",
    });
  }
  throw new AnswerApiError(`Error HTTP ${res.status}: ${detail}`, {
    status: res.status,
    kind: "http",
  });
}

async function fetchJson(url: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(url, init);
  } catch {
    throw new AnswerApiError(
      "No se pudo conectar con la API. ¿Está corriendo el backend?",
      { kind: "network" },
    );
  }
}

export async function createAnswerSession(): Promise<SessionCreated> {
  const res = await fetchJson(`${getApiBaseUrl()}/api/v1/answer/session`, {
    method: "POST",
  });
  if (res.status === 201) {
    return (await res.json()) as SessionCreated;
  }
  throwForFailedResponse(res, await readErrorDetail(res));
}

export async function listAnswerSessions(): Promise<SessionSummary[]> {
  const res = await fetchJson(`${getApiBaseUrl()}/api/v1/answer/sessions`);
  if (res.status === 200) {
    return (await res.json()) as SessionSummary[];
  }
  throwForFailedResponse(res, await readErrorDetail(res));
}

export async function readAnswerSession(
  sessionId: string,
): Promise<SessionView> {
  const res = await fetchJson(
    `${getApiBaseUrl()}/api/v1/answer/session/${encodeURIComponent(sessionId)}`,
  );
  if (res.status === 200) {
    return (await res.json()) as SessionView;
  }
  throwForFailedResponse(res, await readErrorDetail(res));
}

export async function renameAnswerSession(
  sessionId: string,
  title: string,
): Promise<SessionView> {
  const res = await fetchJson(
    `${getApiBaseUrl()}/api/v1/answer/session/${encodeURIComponent(sessionId)}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title }),
    },
  );
  if (res.status === 200) {
    return (await res.json()) as SessionView;
  }
  throwForFailedResponse(res, await readErrorDetail(res));
}

export async function deleteAnswerSession(sessionId: string): Promise<void> {
  const res = await fetchJson(
    `${getApiBaseUrl()}/api/v1/answer/session/${encodeURIComponent(sessionId)}`,
    { method: "DELETE" },
  );
  if (res.status === 204) return;
  throwForFailedResponse(res, await readErrorDetail(res));
}
