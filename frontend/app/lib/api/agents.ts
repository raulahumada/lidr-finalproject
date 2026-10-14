/** Agent catalog + custom profile CRUD via BFF. || Catálogo de agentes y customs vía BFF. */

import { AnswerApiError, getApiBaseUrl } from "./answer";

export type AgentCatalogEntry = {
  key: string;
  label: string;
  role: string;
  llm_driven: boolean;
  tools: string[];
  kind?: "builtin" | "custom";
  mutable?: boolean;
  enabled?: boolean;
  system_prompt?: string;
  prompt_preview?: string | null;
  prompt_note?: string;
  prompt_source?: string;
  prompt_kind?: "jinja" | "none" | "db";
  implementation?: string;
};

export type AgentCatalogResponse = {
  agents: AgentCatalogEntry[];
  ladder: string[];
  domains: string[];
  knobs: {
    agentic_orchestrator_max_steps: number;
    agentic_confidence_threshold: number;
  };
};

export type AgentProfileCreate = {
  key: string;
  label: string;
  role: string;
  system_prompt: string;
  enabled?: boolean;
};

export type AgentProfileUpdate = {
  label?: string;
  role?: string;
  system_prompt?: string;
  enabled?: boolean;
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

function throwHttp(res: Response, detail: string): never {
  throw new AnswerApiError(`Error HTTP ${res.status}: ${detail}`, {
    status: res.status,
    kind: "http",
  });
}

export async function fetchAgentCatalog(): Promise<AgentCatalogResponse> {
  const url = `${getApiBaseUrl()}/api/v1/answer/agents`;
  const res = await fetchJson(url);
  if (res.status === 200) {
    return (await res.json()) as AgentCatalogResponse;
  }
  throwHttp(res, await readErrorDetail(res));
}

export async function fetchAgentDetail(
  key: string,
): Promise<AgentCatalogEntry> {
  const url = `${getApiBaseUrl()}/api/v1/answer/agents/${encodeURIComponent(key)}`;
  const res = await fetchJson(url);
  if (res.status === 200) {
    return (await res.json()) as AgentCatalogEntry;
  }
  throwHttp(res, await readErrorDetail(res));
}

export async function createAgentProfile(
  body: AgentProfileCreate,
): Promise<AgentCatalogEntry> {
  const url = `${getApiBaseUrl()}/api/v1/answer/agents`;
  const res = await fetchJson(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (res.status === 201) {
    return (await res.json()) as AgentCatalogEntry;
  }
  throwHttp(res, await readErrorDetail(res));
}

export async function updateAgentProfile(
  key: string,
  body: AgentProfileUpdate,
): Promise<AgentCatalogEntry> {
  const url = `${getApiBaseUrl()}/api/v1/answer/agents/${encodeURIComponent(key)}`;
  const res = await fetchJson(url, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (res.status === 200) {
    return (await res.json()) as AgentCatalogEntry;
  }
  throwHttp(res, await readErrorDetail(res));
}

export async function deleteAgentProfile(key: string): Promise<void> {
  const url = `${getApiBaseUrl()}/api/v1/answer/agents/${encodeURIComponent(key)}`;
  const res = await fetchJson(url, { method: "DELETE" });
  if (res.status === 204) return;
  throwHttp(res, await readErrorDetail(res));
}
