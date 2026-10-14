/**
 * Server-only relay from the Next BFF to FastAPI.
 *
 * Attaches `Authorization: Bearer SERVICE_TOKEN` and `X-Console-User` from the
 * Auth.js session so the browser never sees AI_SERVICE_URL or the shared secret.
 *
 * || Relay server-only del BFF Next hacia FastAPI.
 * Adjunta Bearer y X-Console-User; el browser nunca ve la URL del API ni el token.
 */
import "server-only";

import { auth } from "@/auth";
import { consoleUserHeaderFor } from "@/lib/ai-service/console-user";
import {
  isAdminUpstreamPath,
  mayCallAdminRoute,
} from "@/lib/auth/roles";

const DEFAULT_TIMEOUT_MS = 60_000;
const LONG_TIMEOUT_MS = 180_000;

function serviceBaseUrl(): string {
  const url = process.env.AI_SERVICE_URL?.trim();
  if (!url) {
    throw new Error("AI_SERVICE_URL no está configurada.");
  }
  return url.replace(/\/$/, "");
}

function serviceAuthHeader(): Record<string, string> {
  // Same secret as backend SERVICE_TOKEN — never NEXT_PUBLIC_.
  const token = process.env.SERVICE_TOKEN?.trim();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function timeoutFor(pathname: string, method: string): number {
  if (
    method === "POST" &&
    (pathname.includes("/answer/agentic") || pathname.includes("/ingest/runs"))
  ) {
    return LONG_TIMEOUT_MS;
  }
  return DEFAULT_TIMEOUT_MS;
}

/**
 * Relays a browser request to FastAPI with the service bearer token.
 * Requires an Auth.js session; admin upstream paths need administrador.
 */
export async function relayToAiService(
  request: Request,
  upstreamPath: string,
): Promise<Response> {
  const session = await auth();
  if (!session?.user?.id) {
    return Response.json(
      { error: "Tenés que iniciar sesión.", status: 401 },
      { status: 401 },
    );
  }

  const method = request.method.toUpperCase();
  if (
    isAdminUpstreamPath(upstreamPath) &&
    !mayCallAdminRoute(session.user.role)
  ) {
    return Response.json(
      { error: "Solo un administrador puede ver esto.", status: 403 },
      { status: 403 },
    );
  }

  const url = new URL(request.url);
  const target = `${serviceBaseUrl()}${upstreamPath}${url.search}`;
  const headers: Record<string, string> = {
    ...serviceAuthHeader(),
    ...consoleUserHeaderFor(session.user.id),
  };

  const contentType = request.headers.get("content-type");
  if (contentType) headers["Content-Type"] = contentType;

  const init: RequestInit = {
    method,
    headers,
    cache: "no-store",
    signal: AbortSignal.timeout(timeoutFor(upstreamPath, method)),
  };

  if (method !== "GET" && method !== "HEAD") {
    const body = await request.arrayBuffer();
    if (body.byteLength > 0) init.body = body;
  }

  let upstream: Response;
  try {
    upstream = await fetch(target, init);
  } catch {
    return Response.json(
      { error: "No se pudo contactar al servicio IA.", status: 502 },
      { status: 502 },
    );
  }

  const outHeaders = new Headers();
  const upstreamType = upstream.headers.get("content-type");
  if (upstreamType) outHeaders.set("Content-Type", upstreamType);

  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: outHeaders,
  });
}
