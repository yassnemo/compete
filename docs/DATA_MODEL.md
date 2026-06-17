# Data Model

The warehouse is a single DuckDB file with three layers: a pipeline-owned
**raw** schema, a dbt **staging** schema (views), and a dbt **marts** schema
(tables). Parquet under `data/raw/` is the durable landing zone (see ADR 0001).

## Lineage

```
config/competitors.yaml
        │  (collectors)
        ▼
raw.raw_pages ──┐                         data/raw/*.parquet  (landing zone)
raw.competitors │
                │  (detect + LLM extract)
                ▼
raw.signals · raw.changes · raw.llm_calls
                │
   ┌────────────┴───────── dbt staging (views) ─────────────┐
   stg_raw_pages · stg_signals · stg_changes · stg_competitors
                │
   ┌────────────┴───────────── dbt marts (tables) ──────────┐
   dim_competitors        fct_changes          fct_hiring
   fct_pricing_history    agg_weekly_competitor fct_signal_duplicates
```

Generated dbt docs (catalog + lineage graph): from `warehouse/dbt/` run
`dbt docs generate` then `dbt docs serve`. The catalog is written to
`warehouse/dbt/target/catalog.json`.

## Raw layer (`raw.*`, written by the pipeline)

| Table | Grain | Key columns |
|-------|-------|-------------|
| `raw_pages` | one fetched snapshot of a URL | `id` (=hash(url, content)), `competitor_id`, `url`, `source_type`, `raw_html`, `clean_text`, `content_hash`, `fetched_at` |
| `competitors` | one competitor | `competitor_id`, `name`, `domain`, `industry`, `tier`, `tracked_urls` (JSON) |
| `signals` | one extracted signal per changed snapshot | `id` (=hash(url, source_hash)), `signal_type`, `title`, `summary`, `entities` (JSON), `significance`, `confidence`, `embedding` (FLOAT[]), `source_hash`, `model`, `extracted_at` |
| `changes` | one detected change | `change_id`, `change_type` (new/updated/removed), `summary`, `significance_score`, `prev_hash`, `new_hash`, `detected_at` |
| `llm_calls` | one LLM API call | `provider`, `model`, token counts, `latency_ms`, `ok`, `error` |

## Staging (`main_staging.*`, dbt views)

Type-cast, lightly cleaned passthroughs: `stg_raw_pages`, `stg_signals`
(carries the embedding), `stg_changes`, `stg_competitors` (adds
`tracked_url_count`). Source freshness/uniqueness tests live in
`models/staging/_sources.yml` and `_staging.yml`.

## Marts (`main_marts.*`, dbt tables)

| Mart | Grain | Notes |
|------|-------|-------|
| `dim_competitors` | competitor | Adds `signal_count`, `high_significance_count`, `last_signal_at`. |
| `fct_changes` | change | Joins the signal's `title`/`confidence`/`entities`; adds **`weighted_significance`** (model significance + 1 for funding/launch/pricing/leadership, capped at 5). Powers the changes feed + ranking. |
| `fct_hiring` | job posting | Parsed from `source_type='jobs'` snapshots: `role`, `location` (from the "Role (Location)" first line), `posted_at`. `removed_at` reserved for run-over-run removal detection (future). |
| `fct_pricing_history` | price point | Heuristic recovery of `plan`/`price`/`currency` from `pricing_change` signals. Sparse by design - the base `Signal` schema has no structured price field; richer history needs dedicated pricing extraction. |
| `agg_weekly_competitor` | competitor × week | `total_changes`, `high_significance_changes`, `new`/`updated` counts, `avg_significance`, `top_significance`. Feeds dashboard trends + weekly report. |
| `fct_signal_duplicates` | signal pair | Embedding near-duplicates within (competitor, signal_type) via `list_cosine_similarity ≥ 0.95`. Enables de-duplication so one announcement isn't double-counted. |

## Significance scoring

The LLM assigns each `Signal` a `significance` (1-5). `fct_changes` derives
`weighted_significance` by boosting strategically important signal types, which
is what the dashboard and report rank on. This keeps scoring deterministic and
in SQL (auditable), not hidden in a prompt.

## Data-quality tests

`dbt test` (run as part of `dbt build`) enforces: uniqueness/not-null on all
keys, `accepted_values` for `change_type` and `signal_type`, `significance` and
`weighted_significance` within 1-5, and source-level uniqueness on raw ids.
Current suite: **40 tests, all passing.**
