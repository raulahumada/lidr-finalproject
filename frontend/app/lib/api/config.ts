/** Thin client for /api/v1/config/models */

import { AnswerApiError, getApiBaseUrl } from "./answer";

export type RoleModelView = {
  effective: string;
  default: string;
  overridden: boolean;
};

export type ModelsConfig = {
  models: Record<string, RoleModelView>;
  available_models: string[];
  embedding_model: string;
  embedding_model_note: string;
};

export type ModelsUpdate = {
  models: Record<string, string | null>;
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

function raise(res: Response, detail: string): never {
  if (res.status === 503) {
    throw new AnswerApiError(
      detail ||
        "Config de modelos no disponible (503). ¿Redis está arriba?",
      { status: 503, kind: "unavailable" },
    );
  }
  throw new AnswerApiError(`Error HTTP ${res.status}: ${detail}`, {
    status: res.status,
    kind: "http",
  });
}

export async function getModelsConfig(): Promise<ModelsConfig> {
  const url = `${getApiBaseUrl()}/api/v1/config/models`;
  let res: Response;
  try {
    res = await fetch(url);
  } catch {
    throw new AnswerApiError(
      "No se pudo conectar con la API. ¿Está corriendo el backend?",
      { kind: "network" },
    );
  }
  if (!res.ok) raise(res, await readErrorDetail(res));
  return (await res.json()) as ModelsConfig;
}

export async function putModelsConfig(
  body: ModelsUpdate,
): Promise<ModelsConfig> {
  const url = `${getApiBaseUrl()}/api/v1/config/models`;
  let res: Response;
  try {
    res = await fetch(url, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new AnswerApiError(
      "No se pudo conectar con la API. ¿Está corriendo el backend?",
      { kind: "network" },
    );
  }
  if (!res.ok) raise(res, await readErrorDetail(res));
  return (await res.json()) as ModelsConfig;
}
