# ADR 0003 - Deterministic pipeline over an autonomous agent

- **Status:** Accepted
- **Date:** 2026-06-07

## Context

"Agentic" systems range from autonomous, tool-using, free-roaming agents to
narrow, deterministic pipelines that call an LLM for one well-defined task. This
project values reliability, debuggability, and low cost.

## Decision

Build a **deterministic pipeline** (`collect → detect → extract → warehouse →
serve`) where the LLM is used **only** for structured extraction: turning
already-known-changed content into a validated `Signal`. No autonomous planning,
no open-ended tool use, no self-directed crawling.

The single agentic behaviour is a **validation-retry loop**: if the LLM output
fails Pydantic validation, retry once with the error message fed back.

## Consequences

**Positive**
- Every stage is independently runnable and unit-testable; failures are
  localized.
- Costs are predictable and bounded (extraction only on real changes).
- No prompt-injection-driven action risk - the LLM can't take actions, only
  return data that is then validated.
- Easy to port to an orchestrator (Prefect) later without rewrites.

**Negative / trade-offs**
- Less "magic" / flexibility than an autonomous agent; new behaviours require
  code, not just prompting.
- Crawl targets are config-driven, not discovered autonomously (intentional -
  scraping ethics and predictability).

## Alternatives considered

- **Autonomous agent** that decides what to scrape and when - harder to make
  reliable/cheap, opaque failures, and an ethics/safety liability for scraping.
