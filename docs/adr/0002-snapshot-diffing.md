# ADR 0002 - Snapshot-diffing over naive re-extraction

- **Status:** Accepted
- **Date:** 2026-06-07

## Context

Competitor pages are re-fetched on a schedule. Running the LLM on every fetch
would be wasteful and expensive - most fetches return identical or trivially
changed content (timestamps, nonces, rotating banners).

## Decision

Gate LLM extraction behind a **two-stage cheap diff**:

1. **Content hash** - normalize text, SHA-256 it. If the hash matches the
   previous snapshot, stop. No change.
2. **Embedding cosine similarity** - if the hash differs, embed the new and
   previous cleaned text. High similarity (above a threshold) ⇒ a minor edit,
   skip extraction. Low similarity ⇒ a real change ⇒ extract a `Signal` and
   record a `fct_changes` row.

Both stages are pure Python / dbt - **the LLM never decides whether something
changed.**

## Consequences

**Positive**
- LLM spend scales with *meaningful* changes, not fetch frequency.
- Deterministic, testable change detection (hash + cosine are reproducible).
- Embeddings double as semantic-dedup signal across competitors.

**Negative / trade-offs**
- A similarity threshold must be tuned; too high misses real changes, too low
  wastes calls. Threshold is configurable and logged.
- Requires storing prior snapshots (cheap in DuckDB/Parquet).

## Alternatives considered

- **Re-extract every fetch** - simplest, but cost grows linearly with schedule
  frequency and most calls are redundant.
- **Hash only** - misses the "minor edit vs real change" distinction; a single
  changed character would trigger a full extraction.
