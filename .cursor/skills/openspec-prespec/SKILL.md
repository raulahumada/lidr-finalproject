---
name: openspec-prespec
description: >-
  Draft a change before OpenSpec propose: sync course reference architecture,
  classify frontend vs backend scope, iterate a draft spec, then run the full
  OpenSpec propose flow on approval. Use when the user runs /opsx-prespec,
  asks for a prespec/pre-propose draft, or wants a grounded draft with
  front/back discrimination before OpenSpec artifacts.
license: MIT
compatibility: Requires openspec CLI, git, and network access to GitHub.
metadata:
  author: entrega-lidr
  version: "1.0"
---

# OpenSpec prespec (draft → iterate → propose)

Two-phase workflow. **Do not** create an OpenSpec change until the user approves the draft.

| Phase | Goal | OpenSpec? |
|-------|------|-----------|
| **A — Draft** | Sync course ref, classify surface, write draft spec | No |
| **B — Propose** | On explicit approval, run full propose (proposal/design/specs/tasks) | Yes |

Companion command: `/opsx-prespec`.

---

## Reference repo (course architecture)

| Key | Value |
|-----|-------|
| Remote | `https://github.com/LIDR-academy/ai-engineering.git` |
| Default branch | `session_16` |
| Sparse path | `ai-service` |
| Local cache | `.reference/ai-engineering/` (gitignored) |

Use that tree as **architecture reference** (layers, patterns), not code to copy verbatim. Domain/corpus stay Metropol Fintech (`README.md`, `AGENTS.md`).

Override branch/path only if the user names another session or folder.

### Sync step (always at start of Phase A)

Run the helper from repo root. **Default host is macOS/Linux (bash)** — do not assume PowerShell.

```bash
bash .cursor/skills/openspec-prespec/scripts/sync-reference.sh
```

Optional args: `bash …/sync-reference.sh <branch> <sparsePath>` (defaults: `session_16` `ai-service`).

Windows only (if `powershell` / `pwsh` is available):

```powershell
powershell -NoProfile -File .cursor/skills/openspec-prespec/scripts/sync-reference.ps1
```

If the script fails, fall back to browsing the GitHub tree URL from `openspec/config.yaml` and note that the local cache is stale/missing. Continue with local monorepo + whatever reference you can read.

After sync, skim `.reference/ai-engineering/ai-service/` (or the sparse path) for folders/files relevant to the user's idea. Prefer reading layout and a few key modules over dumping the whole tree.

---

## Graphify (local knowledge graph)

This monorepo has **Graphify** installed for Cursor (CLI `graphify`, rule `.cursor/rules/graphify.mdc`). Output lives in `graphify-out/` (gitignored).

**Always ground Phase A (and Phase B seeding) with Graphify before broad Grep/Glob exploration**, when the change touches existing code or architecture:

1. If `graphify-out/graph.json` exists, run from repo root (PATH must include `~/.local/bin` if needed):
   ```bash
   graphify query "<intent or module focus of the change>"
   # optional, when comparing two symbols/modules:
   graphify path "<A>" "<B>"
   graphify explain "<concept>"
   ```
2. Prefer Graphify for: who calls what, community hubs, cross-file edges (EXTRACTED vs INFERRED), where a feature already lives.
3. Use Read/Grep/Glob after Graphify orients you, or when you need exact lines to edit.
4. If `graphify-out/graph.json` is missing: note it in the draft Open questions; optionally run `graphify update .` (AST-only, no API) or tell the user to run `/graphify .` for a full rebuild. Do **not** block the draft on a full rebuild unless the user asks.
5. After proposing a change that will reshape modules, mention in the Phase B summary that apply should end with `graphify update .` so the graph stays current.

Capture useful hits in the draft under **Graphify notes** (paths, god nodes, communities, edges that constrain the design).

---

## Surface discrimination (front / back / both)

Classify **before** writing the draft. State it explicitly every time.

| Surface | When | Touch |
|---------|------|--------|
| `backend` | API, RAG, agents, orchestration, schemas, config, Python services | `backend/` |
| `frontend` | UI, pages, Astryx components, client UX | `frontend/` |
| `both` | Contract + UI, E2E feature, API consumed by new screens | `backend/` + `frontend/` |

Rules:

1. Infer from the user request + local tree + course reference (e.g. API layers → backend; chat UI → frontend).
2. If ambiguous, ask once with options: backend / frontend / both — then continue.
3. Never invent shared packages or cross-folder glue unless the user asks (`AGENTS.md`).
4. Frontend work must follow `frontend/AGENTS.md` (Astryx), not ad-hoc layout CSS.
5. Backend work should extend existing routers/patterns under `backend/app/` when possible.
6. Record primary surface and optional secondary in the draft and later in OpenSpec artifacts (Impact / tasks grouping).

---

## Input

Argument after `/opsx-prespec` (or the user message): change name (kebab-case) **or** a description.

If empty, ask what they want to build/fix. Derive kebab-case name (e.g. `add retrieval endpoint` → `add-retrieval-endpoint`).

**Do not** proceed without a clear intent.

---

## Phase A — Draft (no OpenSpec change yet)

1. **Sync** course reference (script above).
2. **Classify** surface: `backend` | `frontend` | `both`.
3. **Ground with Graphify** (see above): query the graph for the change intent; record hubs/paths that matter.
4. **Ground** in this repo: read relevant files under `backend/` and/or `frontend/` per surface (narrowed by Graphify when available).
5. **Ground** in the reference repo: note which paths/patterns inform the approach.
6. **Write draft** to:

   ```text
   openspec/drafts/<name>.md
   ```

   Create `openspec/drafts/` if needed. Use the template below.
7. **Show** the user a short summary + path to the draft.
8. **Stop and wait** for feedback. Phrases like "cambiá X", "sacá Y", "más foco en front" → edit the draft only, stay in Phase A.
9. **Do not** run `openspec new change` until Phase B.

### Draft template

```markdown
# Draft: <name>

## Surface
- Primary: backend | frontend | both
- Paths in this repo: …
- Course reference (branch/path): …
- Patterns borrowed (not copied): …

## Intent
What & why (short).

## Graphify notes
- Queried: …
- Hubs / communities: …
- Relevant paths / edges (EXTRACTED vs INFERRED): …
- Gaps (graph missing / stale / no hit): … | None

## Non-goals
…

## Draft requirements
- …

## Approach sketch
How it would land in this monorepo, aligned to course layers where relevant.
Prefer extending nodes/modules Graphify already surfaces; call out new islands.

## Practices check (backend | both only)
If surface includes backend, read `docs/python-best-practices.md` and fill:
- Aligned: …
- Deviations (+ why): … | None
- Risks if ignored: …

## Impact
- backend: …
- frontend: …
- (omit empty)

## Open questions
- …

## Status
- [ ] User approved — ready for OpenSpec propose
```

---

## Phase B — Full OpenSpec propose (only after approval)

Triggers (explicit): "dale", "ok", "aprobado", "arrancá openspec", "propose", "listo para propose", `/opsx-propose`, or clear go-ahead.

Then follow the same flow as `openspec-propose` / `/opsx-propose`:

1. `openspec new change "<name>"`
2. `openspec status --change "<name>" --json` — use `applyRequires`, `artifacts`, `planningHome`, `changeRoot`, `artifactPaths`.
3. For each ready artifact: `openspec instructions <id> --change "<name>" --json` → write to `resolvedOutputPath` using `template`; apply `context`/`rules` as constraints only (never paste those blocks into files).
4. Seed artifacts from the **approved draft** (`openspec/drafts/<name>.md`): surface, requirements, reference notes, **Graphify notes**, impact split, **Practices check**.
5. Re-run a focused `graphify query` if the draft is stale or Phase B needs fresher edges; fold findings into design decisions.
6. If surface is `backend` or `both`: re-read `docs/python-best-practices.md` and ensure proposal/design include the Practices check and layer mapping (same rules as `/opsx-propose`).
7. In `design.md`, cite Graphify-backed module relationships when explaining where code lands (do not dump raw query output).
8. Group `tasks.md` by surface (`## Backend`, `## Frontend`) when `both`.
9. Re-check status until `applyRequires` are done.
10. Summarize: change name, artifacts, surface, Graphify grounding used (or skipped + why), prompt to `/opsx-apply` (and `graphify update .` after apply).

**Store selection:** If the user names a store, `openspec store list --json` and pass `--store <id>` on change/spec commands. Otherwise nearest local `openspec/`.

After a successful propose, optionally mark the draft status checked or add a line `Promoted to openspec change <name>`. Do not delete the draft unless the user asks.

---

## Guardrails

- Phase A = draft + iterate only; no app code, no `openspec new change`.
- Phase B requires explicit user approval.
- Course repo = reference patterns; product domain = Metropol Fintech.
- Always state surface (`backend` / `frontend` / `both`) in draft and in proposal impact.
- Backend|both drafts and proposals must contrast against `docs/python-best-practices.md`.
- Prefer Graphify (`query` / `path` / `explain`) before broad codebase search when `graphify-out/graph.json` exists; record notes in the draft.
- If a change with that name already exists, ask: continue it, new name, or replace draft only.
- Prefer reasonable decisions over endless questions; ask only when surface or intent is blocked.
