# ADR 0001 - DuckDB over Postgres for the warehouse

- **Status:** Accepted
- **Date:** 2026-06-07

## Context

We need an analytical store for snapshots, signals, and dimensional marts that
dbt can build on. Options: a hosted Postgres (e.g. Supabase free tier) or an
embedded analytical engine (DuckDB).

## Decision

Use **DuckDB** as the analytical warehouse, with **Parquet** for the raw/staging
layer. dbt uses `dbt-duckdb` against the same file.

## Consequences

**Positive**
- Zero infrastructure / zero cost - a single `.duckdb` file, no server.
- Columnar + vectorized: fast aggregations for the dashboard and reports.
- First-class Parquet, JSON, and a VSS extension for embeddings - no separate
  vector DB needed.
- Trivial to reproduce locally and in CI (GitHub Actions).

**Negative / trade-offs**
- Single-writer model: not suited to high-concurrency OLTP. Mitigated by having
  the pipeline be the sole writer and the API read-only (or short-lived writes
  for config CRUD).
- Not a hosted service. For a hosted operational store we document Supabase as
  an optional add-on, but the default keeps everything file-based.

## Alternatives considered

- **Supabase Postgres** - nice hosted CRUD + realtime, but adds infra, network
  latency for analytics, and a moving part the demo doesn't need. Documented as
  optional in DEPLOYMENT.md.
