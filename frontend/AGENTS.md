<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

<!-- ASTRYX:START -->
Astryx v0.6.8 · 168 components
CLI: run every command as `npx astryx <cmd>` (shown below as `astryx ...`).

SETUP (once, in app entry e.g. main.tsx) — without these, components render unstyled:
  import "@astryxdesign/core/reset.css";
  import "@astryxdesign/core/astryx.css";

WORKFLOW — start every page from a template, never from scratch:
1. `astryx build "<idea>"` — names the template to scaffold from and the parts it lacks.
2. `astryx template <name> <path>` — scaffold it; keep its frame, gap and padding; replace the content.
3. `astryx template <Block>` for parts it lacks; `astryx component <Name>` to read props before using one.
Changing an existing page? Keep it: skip step 2 and add blocks/components inside its sections.

RULES:
- No <div> — components handle all layout and spacing.
- Read `astryx docs layout` before changing a template's frame.
- Dense data = rows (Table, List/Item), not Card-wrapped lists. Badge = counts only.
- Style with component props first, then Tailwind utilities backed by tokens. No raw hex/px.
- Palettes and custom colors go through the theme, never :root overrides. See `astryx docs theme`.
- SELF-CHECK: re-read the file; replace any style={{…}}, raw <div>/<span>, imported .css/@apply, or hardcoded/arbitrary value (bg-[#fff], p-[13px]) with the component or a token-backed utility.

`astryx help` lists every command. Key ones beyond the workflow:
  search "<query>"   find any component / hook / doc / template
  discover <words>   integrations you could add
  docs <topic>       getting-started, principles, tokens, theme … (`astryx docs` lists all)
  docs cli           commands, API reference, integration authoring
  upgrade --from <old version> --apply   run after a dependency bump
<!-- ASTRYX:END -->

## Auth + BFF (dual authentication)

Two layers (not interchangeable):

1. **Console people** — Auth.js (email/password; Google deferred) + Prisma identity DB (`AUTH_DATABASE_URL`).
2. **Service token** — FastAPI `SERVICE_TOKEN`; the Next BFF attaches `Authorization: Bearer` server-side. Never `NEXT_PUBLIC_SERVICE_TOKEN`.

Browser clients call same-origin `/api/v1/...` (`getApiBaseUrl()` → `""`). Route handler `app/api/v1/[...path]` relays to `AI_SERVICE_URL` with the token + `X-Console-User` (Auth.js user id). That header scopes chat sessions: each operator only lists/opens their own conversations in the SideNav. Smoke: two users → each sees only their chats; deep-link to the other’s `?session=` → empty/404.

### Setup (identity DB)

```bash
# From repo root — second database on the same Compose Postgres:
set -a && source .env && set +a
docker compose exec postgres psql -U "$POSTGRES_USER" -c "CREATE DATABASE entrega_lidr_auth;"

cd frontend
cp .env.example .env.local   # AUTH_SECRET, AUTH_DATABASE_URL, AI_SERVICE_URL, SERVICE_TOKEN
npm run db:generate
npm run db:migrate
AUTH_SEED_PASSWORD='your-long-password' npm run seed:admin -- admin@example.com
npm run dev
```

Roles: `usuario` (answer/search/home) · `administrador` (+ settings/ingest/agents/users). New self-registrations are **disabled** until an admin enables them on `/users`.

### Modes

| Mode | `SERVICE_TOKEN` (backend + frontend `.env.local`) | Console |
|------|--------------------------------------------------|---------|
| Open local | empty | still requires Auth.js login; FastAPI accepts curl without Bearer |
| Locked | same non-empty secret in both | UI via login; curl to `:8000` without Bearer → 401; `GET /api/v1/health` → 200 |

Smoke locked: seed admin → login → `/ingest` ok as admin; open `/settings` as `usuario` → redirect; `curl :8000/api/v1/search` without Bearer → 401.

## Home (`/`)

Entrada de producto Metropol (Astryx): título + copy corto + CTAs a **Chat** (`/answer`), **Agentes** (`/agents`), **Búsqueda** (`/search`) e **Ingesta** (`/ingest`). Sin boilerplate de create-next-app.

Smoke: abrir `/` → “Abrir chat” llega a `/answer`; “Agentes”, “Búsqueda” e “Ingesta” a sus rutas.

## Agentic answer chat (`/answer`)

Primary path is **agentic live progress** + **multi-sesión** + **orquestador star** (Astryx `ai-chat` frame: session list, domain override, suggestions, live agent steps, routing, Markdown, evidence, human gate):

| Action | Endpoint |
|--------|----------|
| Sessions | `POST/GET/PATCH/DELETE {API}/api/v1/answer/session*` · `GET …/sessions` |
| Start | `POST {API}/api/v1/answer/agentic/start` (+ optional `session_id`, optional `domain`) → 202 + `thread_id` |
| Progress poll (~1.2s) | `GET {API}/api/v1/answer/agentic/{thread_id}/progress` |
| Resume (approve / reject / adjust) | `POST {API}/api/v1/answer/agentic/{thread_id}/resume` |
| Agents catalog | `GET {API}/api/v1/answer/agents` → UI `/agents` |

- **`session_id` ≠ `thread_id`:** sesión = conversación durable (transcript); thread = un run del grafo.
- **Domain tag** (Selector en el composer): `auto` no manda `domain`; `ventas|cobranzas|operacion|tenela|general` se envía en el start. El chip muestra el dominio efectivo del progress/respuesta.
- **Jerarquía del turno:** respuesta → aportes custom → evidencia → **Flujo / auditoría** (`Collapsible` con ruteo + tool calls). Domain badge siempre visible. Audit abierta en vivo; colapsada al terminar.
- **Aportes custom:** List “Aportes custom” (key + nota wrapping, preview ~400 chars); persisten en history. Smoke: crear custom en `/agents` → preguntar en `/answer` → leer la respuesta primero, expandir auditoría si hace falta, ver nota y evidencia.
- Sesiones en el **SideNav del AppShell** (sección Conversaciones), no un segundo sidebar.
- Podés cambiar de sesión mientras corre un run: **no se cancela**; el poll sigue y al volver ves el resultado / history.
- Deep link: `/answer?session=<id>` restaura el history desde el backend.
- The UI does **not** ask for `k`; the backend default applies.
- Hot path: `runAgenticWithProgress` in `lib/api/agentic.ts` (start + poll with `session_id` / `domain`). Clients in `lib/api/sessions.ts` y `lib/api/agents.ts`.
- While `status=running`, the chat shows `ChatToolCalls` for Metropol nodes (incluye `orchestrator`).
- Terminal `awaiting_human_review` is a pause, not an error. Resume is a direct POST (no poll); al cerrar el turno se appendea al transcript de la sesión.

### Agents console (`/agents`)

SideNav → **Agentes**. Studio master-detail (grafo + panel):

- **Grafo estrella:** hub orquestador + fila de nodos del ladder (ClickableCard). Click = detalle.
- **Builtin:** solo lectura. Solo `grounded_composer` muestra system prompt (Jinja `CodeBlock`). El resto es código → banner “Sin system prompt”.
- **Custom:** tab Crear / editar / borrar / enable (Postgres); enabled → nodo en el ladder tras `corpus_fetcher`.
- Knobs (max steps / confidence) debajo del grafo.

Smoke: abrir `/agents`, click orquestador vs composer (ver diferencia de prompt), crear `risk_advisor`, verlo como nodo, editar, deshabilitar, borrar.

### Search console (`/search`)

SideNav → **Búsqueda**. Consola de retrieve semántico sobre `POST /api/v1/search` (sin generar respuesta):

- Formulario: consulta + `k` (default 5) → lista de hits (score, path, excerpt).
- Estados: loading, vacío (0 hits), error (incl. 503 sin `OPENAI_API_KEY`).
- Deep link: `/search?q=handoff+cobranzas` prefilla y dispara la búsqueda al cargar.
- Cliente: `lib/api/search.ts`.

Smoke: backend up + corpus ingerido → `/search` → “handoff cobranzas” → ver hits con score/path; probar `?q=tenela`; apagar API key → 503 visible en banner.

### Ingest console (`/ingest`)

SideNav → **Ingesta**. Lanza el mismo pipeline que `python -m app.ingestion.run_ingest` vía HTTP:

| Action | Endpoint |
|--------|----------|
| Stats | `GET {API}/api/v1/ingest/stats` |
| Start | `POST {API}/api/v1/ingest/runs` `{ force }` → 202 + `run_id` |
| Poll (~1.2s) | `GET {API}/api/v1/ingest/runs/{run_id}` |

- Switch **Force**, botón Ingerir, resumen (seen/ingested/chunks/skips/errors), CTA a `/search`.
- 503 (config) y 409 (busy) en banner. Jobs in-process (se pierden al reload del API).
- Cliente: `lib/api/ingest.ts` (`runIngestWithProgress`).

Smoke: backend up + `CORPUS_ROOT` + key → `/ingest` → ver docs/chunks → Ingerir (sin force si ya indexado) → summary → “Ir a búsqueda”.

### AI settings (`/settings`)

SideNav → **Ajustes**. Overrides de modelos de chat por rol (`chat` / `composer` / `prompt_specialist`) vía Redis:

| Action | Endpoint |
|--------|----------|
| Load | `GET {API}/api/v1/config/models` |
| Save | `PUT {API}/api/v1/config/models` `{ models: { role: id \| null } }` |

- Selectores Astryx + “Default (.env / cascada)”; embedding solo lectura.
- 503 si Redis no persiste. Cliente: `lib/api/config.ts`.

Smoke: Redis up → `/settings` → cambiar composer a `gpt-4o` → Guardar → badge override → preguntar en `/answer`.

### Checkpointer / activity caveat

Backend **pause/resume** uses a durable Postgres checkpointer by default (`DATABASE_URL`); a paused `thread_id` can still be resumed after an API restart. The **activity/progress log** is still **in-process** — after reload, `/progress` may **404** even though `resume` with a known `thread_id` still works. El **historial de sesión** sí sobrevive F5.
