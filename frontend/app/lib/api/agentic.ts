/** Thin client for agentic answer + live progress — types mirrored from backend schemas */

import {
  AnswerApiError,
  getApiBaseUrl,
  type Citation,
} from "./answer";

export type MetropolDomain =
  | "ventas"
  | "cobranzas"
  | "operacion"
  | "tenela"
  | "general";

export type AgenticAnswerRequest = {
  question: string;
  k?: number;
  session_id?: string;
  /** Omit or leave unset for auto-detect; never send `"auto"`. */
  domain?: MetropolDomain;
};

export type RoutingHistoryEntry = {
  step: number;
  next_agent: string;
  reason: string;
  source: string;
};

export type AgenticResumeRequest = {
  decision: "approve" | "reject" | "adjust";
  note?: string;
  adjusted_answer?: string;
};

export type AgentTraceStep = {
  node: string;
  summary: string;
};

export type GraphActivityEntry = {
  node: string;
  label: string;
  message: string;
  at: number;
};

export type AgenticAnswerResponse = {
  status: "completed" | "awaiting_human_review" | "rejected";
  thread_id: string;
  question: string;
  domain: string | null;
  answer: string | null;
  citations: Citation[];
  agent_trace: AgentTraceStep[];
  routing_history: RoutingHistoryEntry[];
  review_reasons: string[];
  confidence: number | null;
  no_evidence: boolean;
  citations_valid: boolean | null;
  prompt_version: string | null;
  k: number | null;
  interrupt_payload: Record<string, unknown> | null;
};

export type AgenticStartResponse = {
  status: "running";
  thread_id: string;
};

export type AgenticProgressResponse = {
  status:
    | "running"
    | "completed"
    | "awaiting_human_review"
    | "failed"
    | "rejected";
  thread_id: string;
  activity: GraphActivityEntry[];
  question: string | null;
  domain: string | null;
  answer: string | null;
  citations: Citation[];
  agent_trace: AgentTraceStep[];
  routing_history: RoutingHistoryEntry[];
  review_reasons: string[];
  confidence: number | null;
  no_evidence: boolean;
  citations_valid: boolean | null;
  prompt_version: string | null;
  k: number | null;
  interrupt_payload: Record<string, unknown> | null;
  error: string | null;
};

export const POLL_INTERVAL_MS = 1200;

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

function throwForFailedResponse(res: Response, detail: string): never {
  if (res.status === 503) {
    throw new AnswerApiError(
      "Servicio no disponible (503). Suele faltar OPENAI_API_KEY en el backend.",
      { status: 503, kind: "unavailable" },
    );
  }
  if (res.status === 404) {
    throw new AnswerApiError(
      "Thread desconocido o ya no está en pausa (404). Si reiniciaste el backend, el MemorySaver/activity log perdió el thread.",
      { status: 404, kind: "http" },
    );
  }
  throw new AnswerApiError(`Error HTTP ${res.status}: ${detail}`, {
    status: res.status,
    kind: "http",
  });
}

async function fetchJson(
  url: string,
  init?: RequestInit,
): Promise<Response> {
  try {
    return await fetch(url, init);
  } catch {
    throw new AnswerApiError(
      "No se pudo conectar con la API. ¿Está corriendo el backend?",
      { kind: "network" },
    );
  }
}

/** POST /answer/agentic — sync path (200/202). Kept for curl/tests. */
export async function postAgenticAnswer(
  body: AgenticAnswerRequest,
): Promise<AgenticAnswerResponse> {
  const url = `${getApiBaseUrl()}/api/v1/answer/agentic`;
  const res = await fetchJson(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (res.status === 200 || res.status === 202) {
    return (await res.json()) as AgenticAnswerResponse;
  }

  const detail = await readErrorDetail(res);
  throwForFailedResponse(res, detail);
}

/** POST /answer/agentic/start — HTTP 202 + thread_id immediately. */
export async function startAgenticAnswer(
  body: AgenticAnswerRequest,
): Promise<AgenticStartResponse> {
  const url = `${getApiBaseUrl()}/api/v1/answer/agentic/start`;
  const res = await fetchJson(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (res.status === 202) {
    return (await res.json()) as AgenticStartResponse;
  }

  const detail = await readErrorDetail(res);
  throwForFailedResponse(res, detail);
}

export async function getAgenticProgress(
  threadId: string,
): Promise<AgenticProgressResponse> {
  const url = `${getApiBaseUrl()}/api/v1/answer/agentic/${encodeURIComponent(threadId)}/progress`;
  const res = await fetchJson(url);

  if (res.status === 200) {
    return (await res.json()) as AgenticProgressResponse;
  }

  const detail = await readErrorDetail(res);
  throwForFailedResponse(res, detail);
}

export async function resumeAgenticAnswer(
  threadId: string,
  body: AgenticResumeRequest,
): Promise<AgenticAnswerResponse> {
  const url = `${getApiBaseUrl()}/api/v1/answer/agentic/${encodeURIComponent(threadId)}/resume`;
  const res = await fetchJson(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (res.status === 200) {
    return (await res.json()) as AgenticAnswerResponse;
  }

  const detail = await readErrorDetail(res);
  throwForFailedResponse(res, detail);
}

function progressToAnswer(
  progress: AgenticProgressResponse,
): AgenticAnswerResponse {
  const status =
    progress.status === "awaiting_human_review"
      ? "awaiting_human_review"
      : progress.status === "rejected"
        ? "rejected"
        : "completed";
  return {
    status,
    thread_id: progress.thread_id,
    question: progress.question || "",
    domain: progress.domain,
    answer: progress.answer,
    citations: progress.citations || [],
    agent_trace: progress.agent_trace || [],
    routing_history: progress.routing_history || [],
    review_reasons: progress.review_reasons || [],
    confidence: progress.confidence,
    no_evidence: progress.no_evidence,
    citations_valid: progress.citations_valid,
    prompt_version: progress.prompt_version,
    k: progress.k,
    interrupt_payload: progress.interrupt_payload,
  };
}

export type PollAgenticOptions = {
  intervalMs?: number;
  signal?: AbortSignal;
  onProgress?: (progress: AgenticProgressResponse) => void;
};

/**
 * Start + poll until status leaves `running`.
 * Throws AnswerApiError on failed terminal status or HTTP errors.
 */
export async function runAgenticWithProgress(
  body: AgenticAnswerRequest,
  opts: PollAgenticOptions = {},
): Promise<AgenticAnswerResponse> {
  const intervalMs = opts.intervalMs ?? POLL_INTERVAL_MS;
  const start = await startAgenticAnswer(body);
  const threadId = start.thread_id;

  for (;;) {
    if (opts.signal?.aborted) {
      throw new AnswerApiError("Corrida cancelada", { kind: "network" });
    }

    const progress = await getAgenticProgress(threadId);
    opts.onProgress?.(progress);

    if (progress.status === "running") {
      await new Promise<void>((resolve, reject) => {
        const timer = setTimeout(resolve, intervalMs);
        const onAbort = () => {
          clearTimeout(timer);
          reject(new AnswerApiError("Corrida cancelada", { kind: "network" }));
        };
        if (opts.signal) {
          if (opts.signal.aborted) {
            onAbort();
            return;
          }
          opts.signal.addEventListener("abort", onAbort, { once: true });
        }
      });
      continue;
    }

    if (progress.status === "failed") {
      throw new AnswerApiError(
        progress.error || "La corrida agentic falló en background.",
        { kind: "http", status: 500 },
      );
    }

    return progressToAnswer(progress);
  }
}
