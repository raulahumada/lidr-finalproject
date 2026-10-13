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

## API base URL

Chat UI (`/answer`) calls FastAPI at `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000`). Copy `.env.example` → `.env.local` if you need a different origin. Backend CORS already allows `http://localhost:3000`.

## Agentic answer chat (`/answer`)

Primary path is **agentic live progress** + **multi-sesión** (Astryx `ai-chat` frame: session list, suggestions, live agent steps, Markdown, evidence, human gate):

| Action | Endpoint |
|--------|----------|
| Sessions | `POST/GET/PATCH/DELETE {API}/api/v1/answer/session*` · `GET …/sessions` |
| Start | `POST {API}/api/v1/answer/agentic/start` (+ optional `session_id`) → 202 + `thread_id` |
| Progress poll (~1.2s) | `GET {API}/api/v1/answer/agentic/{thread_id}/progress` |
| Resume (approve / reject / adjust) | `POST {API}/api/v1/answer/agentic/{thread_id}/resume` |

- **`session_id` ≠ `thread_id`:** sesión = conversación durable (transcript); thread = un run del grafo.
- Sesiones en el **SideNav del AppShell** (sección Conversaciones), no un segundo sidebar.
- Podés cambiar de sesión mientras corre un run: **no se cancela**; el poll sigue y al volver ves el resultado / history.
- Deep link: `/answer?session=<id>` restaura el history desde el backend.
- The UI does **not** ask for `k`; the backend default applies.
- Hot path: `runAgenticWithProgress` in `lib/api/agentic.ts` (start + poll with `session_id`). Clients in `lib/api/sessions.ts`.
- While `status=running`, the chat shows `ChatToolCalls` for Metropol nodes (pending/running/complete).
- Terminal `awaiting_human_review` is a pause, not an error. Resume is a direct POST (no poll); al cerrar el turno se appendea al transcript de la sesión.

### Checkpointer / activity caveat

Backend **pause/resume** uses a durable Postgres checkpointer by default (`DATABASE_URL`); a paused `thread_id` can still be resumed after an API restart. The **activity/progress log** is still **in-process** — after reload, `/progress` may **404** even though `resume` with a known `thread_id` still works. El **historial de sesión** sí sobrevive F5.
