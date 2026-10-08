---
name: /opsx-prespec
id: opsx-prespec
category: Workflow
description: >-
  Draft a change before OpenSpec (sync course reference, classify front/back),
  iterate the draft, then run full OpenSpec propose on approval
---

Prespec: draft grounded in the course reference architecture, then OpenSpec propose.

**Follow the skill** `.cursor/skills/openspec-prespec/SKILL.md` end-to-end.

## Flow

1. **Phase A — Draft** (no OpenSpec change yet)
   - Sync course reference (macOS/Linux):  
     `bash .cursor/skills/openspec-prespec/scripts/sync-reference.sh`  
     (Windows: sibling `sync-reference.ps1` if PowerShell is available)
   - Classify surface: `backend` | `frontend` | `both`
   - Ground in this monorepo + `.reference/ai-engineering/`
   - Write `openspec/drafts/<name>.md`
   - Show summary and **wait** for user edits / approval

2. **Iterate** — apply user feedback only to the draft until they approve

3. **Phase B — Propose** — only after explicit approval ("dale", "ok", "arrancá openspec", "propose", …)
   - Same artifact pipeline as `/opsx-propose` (`openspec new change`, instructions, proposal/design/specs/tasks)
   - Seed from the approved draft; split tasks by Backend / Frontend when `both`
   - If `backend` | `both`: contrast against `docs/python-best-practices.md` (Practices check in proposal; layer map in design)

## Input

Argument after `/opsx-prespec`: kebab-case name **or** description of what to build/fix.

If missing, ask what they want to change.

## Guardrails

- Do **not** run `openspec new change` in Phase A
- Do **not** implement application code in this command
- Course repo = architecture reference; domain = Metropol Fintech
- Always state primary surface (and secondary if any)
- Backend|both must read and contrast `docs/python-best-practices.md`
