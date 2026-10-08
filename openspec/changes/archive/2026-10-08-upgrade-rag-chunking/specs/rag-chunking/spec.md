# rag-chunking

## Purpose

Splits extracted document text into embeddable chunks using strategies aligned with retrieval quality (recursive default and structural splits for Markdown), including light text normalization before splitting.

## ADDED Requirements

### Requirement: Normalize text before chunking
The chunking pipeline SHALL normalize extracted text before splitting by trimming, collapsing runs of three or more newlines into two, and applying a documented light heuristic suitable for PDF line breaks when processing pdf-sourced text (or shared normalize used for all types that includes safe line-join rules).

#### Scenario: Excessive blank lines are collapsed
- **WHEN** extracted text contains four consecutive newlines between paragraphs
- **AND** chunking runs
- **THEN** the normalized text does not retain four consecutive newlines before splitting

### Requirement: Recursive default strategy
For plain prose sources (at least `txt`, `pdf`, and `docx`), the system SHALL split with a recursive separator hierarchy preferring paragraphs, then lines, then sentences, then spaces, targeting approximately 512 tokens per chunk with approximately 10–20% overlap.

#### Scenario: Long prose yields multiple recursive chunks
- **WHEN** a long multi-paragraph document is chunked with the default strategy
- **THEN** more than one chunk is produced
- **AND** each chunk has non-empty content
- **AND** chunk metadata records the strategy as recursive (or equivalent documented name)

### Requirement: Markdown structural chunking
For Markdown sources (`md`), the system SHALL split on heading levels (at least `#`, `##`, `###`) so that heading boundaries define section chunks, and SHALL apply recursive splitting inside a section when that section exceeds the target size.

#### Scenario: Headings bound sections
- **WHEN** a Markdown document with two `##` sections is chunked
- **THEN** content under different `##` headings is not required to live in the same chunk solely because of character budget
- **AND** chunk metadata may include the section heading when available

### Requirement: Ingest uses the chunking API
Corpus ingest SHALL call the shared chunking API (not the legacy paragraph-only splitter) and persist strategy/section metadata on chunks when available.

#### Scenario: Re-ingest refreshes chunk boundaries
- **WHEN** an operator runs ingest with force after the chunking upgrade
- **THEN** stored chunks reflect the new strategies for newly written documents
