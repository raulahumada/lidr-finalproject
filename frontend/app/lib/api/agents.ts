/** Thin client for GET /answer/agents catalog */

import { AnswerApiError, getApiBaseUrl } from "./answer";

export type AgentCatalogEntry = {
  key: string;
  label: string;
  role: string;
  llm_driven: boolean;
  tools: string[];
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

export async function fetchAgentCatalog(): Promise<AgentCatalogResponse> {
  const url = `${getApiBaseUrl()}/api/v1/answer/agents`;
  let res: Response;
  try {
    res = await fetch(url);
  } catch {
    throw new AnswerApiError(
      "No se pudo conectar con la API. ¿Está corriendo el backend?",
      { kind: "network" },
    );
  }

  if (res.status === 200) {
    return (await res.json()) as AgentCatalogResponse;
  }

  const detail = await readErrorDetail(res);
  throw new AnswerApiError(`Error HTTP ${res.status}: ${detail}`, {
    status: res.status,
    kind: "http",
  });
}
