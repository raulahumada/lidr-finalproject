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

Run the helper (PowerShell from repo root):

```powershell
powershell -NoProfile -File .cursor/skills/openspec-prespec/scripts/sync-reference.ps1
```

Optional: `-Branch session_16` `-SparsePath ai-service`.

If the script fails, fall back to browsing the GitHub tree URL from `openspec/config.yaml` and note that the local cache is stale/missing. Continue with local monorepo + whatever reference you can read.

After sync, skim `.reference/ai-engineering/ai-service/` (or the sparse path) for folders/files relevant to the user's idea. Prefer reading layout and a few key modules over dumping the whole tree.

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
3. **Ground** in this repo: read relevant files under `backend/` and/or `frontend/` per surface.
4. **Ground** in the reference repo: note which paths/patterns inform the approach.
5. **Write draft** to:

   ```text
   openspec/drafts/<name>.md
   ```

   Create `openspec/drafts/` if needed. Use the template below.
6. **Show** the user a short summary + path to the draft.
7. **Stop and wait** for feedback. Phrases like "cambiá X", "sacá Y", "más foco en front" → edit the draft only, stay in Phase A.
8. **Do not** run `openspec new change` until Phase B.

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

## Non-goals
…

## Draft requirements
- …

## Approach sketch
How it would land in this monorepo, aligned to course layers where relevant.

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
4. Seed artifacts from the **approved draft** (`openspec/drafts/<name>.md`): surface, requirements, reference notes, impact split, **Practices check**.
5. If surface is `backend` or `both`: re-read `docs/python-best-practices.md` and ensure proposal/design include the Practices check and layer mapping (same rules as `/opsx-propose`).
6. Group `tasks.md` by surface (`## Backend`, `## Frontend`) when `both`.
7. Re-check status until `applyRequires` are done.
8. Summarize: change name, artifacts, surface, prompt to `/opsx-apply`.

**Store selection:** If the user names a store, `openspec store list --json` and pass `--store <id>` on change/spec commands. Otherwise nearest local `openspec/`.

After a successful propose, optionally mark the draft status checked or add a line `Promoted to openspec change <name>`. Do not delete the draft unless the user asks.

---

## Guardrails

- Phase A = draft + iterate only; no app code, no `openspec new change`.
- Phase B requires explicit user approval.
- Course repo = reference patterns; product domain = Metropol Fintech.
- Always state surface (`backend` / `frontend` / `both`) in draft and in proposal impact.
- Backend|both drafts and proposals must contrast against `docs/python-best-practices.md`.
- If a change with that name already exists, ask: continue it, new name, or replace draft only.
- Prefer reasonable decisions over endless questions; ask only when surface or intent is blocked.
