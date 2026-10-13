# Design

## Context

See proposal.md — Why. `AnswerPageInner` (`frontend/app/answer/page.tsx`) already renders domain, `ChatToolCalls`, routing lists, `CustomNotesList`, Markdown answer, and citations. Graphify hubs: `AnswerPageInner`, `CustomNotesList`; API clients stay consume-only.

## Goals / Non-Goals

**Goals:**
- Clear visual priority: answer first, then notes, then evidence
- Audit (routing + tool calls) behind a collapsible; open while the run is busy
- Astryx-only layout (`Collapsible`, existing Chat/List)

**Non-Goals:**
- Backend/API changes
- `/agents` or home shell redesign
- Changing how notes/citations are fetched or stored

## Decisions

### 1. Content order on assistant turns

**Choice:** Markdown answer (or rejected/review placeholder) → custom notes → citations → audit collapsible.

**Why:** Matches operator demo path (read answer, see specialist input, check sources, optionally expand flow).

**Alt:** Audit above answer — rejected; that is today’s pain.

### 2. Collapsible audit

**Choice:** Astryx `Collapsible` wrapping routing List + `ChatToolCalls`. Label e.g. “Flujo / auditoría”. `defaultIsOpen` true while `isCurrentBusy`, false on terminal/history when audit content exists. Omit the block when there is nothing to show.

**Why:** Keeps live progress visible without permanent noise after completion.

**Alt:** Always expanded — rejected for polish goal.

### 3. Domain badge

**Choice:** Keep domain `Badge` outside the collapsible (always visible when known).

**Why:** Compact context signal; draft default.

### 4. Scope of files

**Choice:** Prefer editing `page.tsx` with a small local helper component; extract a colocated module only if the file becomes harder to scan.

**Why:** Graphify already centers the page; avoid a parallel UI island.

## Risks / Trade-offs

- [Collapsible default open/closed flicker on status flip] → Key by `thread_id` / busy flag; accept uncontrolled default on mount of each phase
- [History has no routing] → Do not render empty audit; notes + evidence order still applies

## Open Questions

None deferred — draft defaults accepted.
