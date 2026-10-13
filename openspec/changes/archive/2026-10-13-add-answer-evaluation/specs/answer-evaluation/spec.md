# answer-evaluation

## Purpose

Provides a Metropol-oriented evaluation harness: a golden question set and deterministic scoring of agentic answer payloads (citations, textual constraints, pause/no-evidence expectations), runnable against a live local API without gating ordinary CI.

## ADDED Requirements

### Requirement: Golden set defines agentic evaluation cases
The repository SHALL include a versioned golden set of Metropol evaluation cases. Each case SHALL have a stable `id`, a non-empty `question`, and may declare optional `domain`, `expect_citations`, `expect_no_evidence`, `expect_pause`, `must_mention`, `must_not_mention`, and human `notes`.

#### Scenario: Case identity
- **WHEN** the golden set is loaded
- **THEN** every case has a unique `id` and a non-empty `question`

### Requirement: Scorer evaluates an agentic payload against a case
Given a golden case and an agentic answer-like payload (`status`, `answer`, `citations`, `citations_valid`, `no_evidence`), the scorer SHALL return a pass/fail result with machine-readable failure reasons. Scoring SHALL be pure (no network, no LLM).

#### Scenario: Citations expected
- **WHEN** a case sets `expect_citations` true
- **AND** the payload has at least one citation and `citations_valid` is not false
- **THEN** the citations expectation passes

#### Scenario: Citations missing
- **WHEN** a case sets `expect_citations` true
- **AND** the payload has zero citations or `citations_valid` is false
- **THEN** the case fails with a reason naming citations

#### Scenario: Must mention
- **WHEN** a case lists `must_mention` substrings
- **AND** the answer text (case-insensitive) contains each substring
- **THEN** the mention expectation passes

#### Scenario: Must not mention
- **WHEN** a case lists `must_not_mention` substrings
- **AND** the answer text (case-insensitive) contains any listed substring
- **THEN** the case fails

#### Scenario: Expect pause
- **WHEN** a case sets `expect_pause` true
- **AND** payload status is `awaiting_human_review`
- **THEN** the pause expectation passes

### Requirement: CLI harness runs cases against a live agentic API
A CLI entrypoint SHALL call the sync agentic answer endpoint for selected golden cases, score each response, write a JSON report, print a summary, and exit 0 only when all executed cases pass. The harness SHALL NOT be required by the default unit-test suite.

#### Scenario: Smoke one case
- **WHEN** the operator runs the harness with a single case id against a reachable base URL
- **THEN** the harness posts that question to agentic answer
- **AND** produces a report entry with pass/fail for that case

#### Scenario: Auto-approve optional
- **WHEN** the harness is run with auto-approve enabled
- **AND** a case returns `awaiting_human_review`
- **THEN** the harness resumes with approve before final scoring of that case
