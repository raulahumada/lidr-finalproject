# home-console-ui

## Purpose

Provides the product home entry for the Metropol operator console: a branded first view with clear navigation into answer chat and agents tooling.

## Requirements

### Requirement: Home presents product entry and primary CTAs
The `/` route SHALL present a Metropol-oriented product title and short supporting text, and SHALL offer actions that navigate to the answer chat (`/answer`) and the agents console (`/agents`). Layout SHALL use Astryx components (no create-next-app boilerplate as the primary content).

#### Scenario: Navigate to answer
- **WHEN** the operator activates the answer CTA on home
- **THEN** the app navigates to `/answer`

#### Scenario: Navigate to agents
- **WHEN** the operator activates the agents CTA on home
- **THEN** the app navigates to `/agents`
