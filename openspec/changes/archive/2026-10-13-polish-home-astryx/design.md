# Design

## Context

See proposal.md. AppShell already hosts nav; `app/page.tsx` is still boilerplate.

## Goals / Non-Goals

**Goals:** One composition home: brand/product signal + short support + CTAs.

**Non-Goals:** Metrics dashboard; auth; redoing `/answer`/`/agents`.

## Decisions

1. Keep AppShell; replace only page content with Astryx Layout/Heading/Button/Empty or landing template.
2. Spanish copy for Metropol / LiDR entrega.
3. CTAs: primary → `/answer`, secondary → `/agents` (and optionally `/search` if that change ships first — link if route exists).

## Risks / Trade-offs

- [Ship home before search] → CTA to search optional / add when route exists
