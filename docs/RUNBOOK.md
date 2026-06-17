# Runbook

Operational procedures for running and maintaining `compete`.

## Prerequisites

```bash
uv sync --extra dev --extra dbt --extra api --extra report
uv run playwright install chromium      # for the dynamic collector
cp .env.example .env                     # Windows: copy .env.example .env
uv run compete init-db
```

## Add a competitor

Two ways - both end up in `raw.competitors`:

1. **Config (version-controlled):** edit `config/competitors.yaml`, then
   ```bash
   uv run compete sync-competitors
   ```
2. **UI / API:** Settings → "Add competitor", or `POST /competitors`.

> After editing `competitors.yaml`, always run `sync-competitors` (or `run-all`)
> so `dim_competitors` reflects the change.

Then collect + extract just that competitor:

```bash
uv run compete collect --competitor <id>
uv run compete extract
```

## Run the full pipeline

```bash
uv run compete run-all                 # sync → collect → extract → dbt → report
uv run compete run-all -p mock -n 5    # offline, capped to 5 URLs/candidates
```

Individual steps: `collect`, `detect` (dry-run, no LLM), `extract`, `report`.

## Backfill / re-extract

- Snapshots are content-addressed; re-running `collect` only stores genuinely
  new content. `extract` skips any `(url, content_hash)` already in
  `raw.signals`, so re-runs are cheap and idempotent.
- To force re-extraction of everything: `DELETE FROM raw.signals;` then
  `uv run compete extract` (DuckDB CLI or `uv run python -c "..."`).
- To rebuild marts after manual changes: `cd warehouse/dbt && dbt build`.

## Fix a broken scraper

Symptoms: `collect` reports `failed` for a URL, or signals stop appearing.

1. Identify the source type in `competitors.yaml`.
2. Test the URL in isolation:
   ```bash
   uv run python -c "from pipeline.collect.static import StaticCollector as C; print(C().collect('x','https://…'))"
   ```
   (swap `static` for `dynamic` / `rss`; jobs uses ATS APIs - verify the board token.)
3. Common causes & fixes:
   - **JS-rendered content empty** → change `source_type` to `dynamic`.
   - **403 / blocked** → the site may disallow bots; check `robots.txt` (we honor
     it). Do not bypass. Consider an official feed/API instead.
   - **Jobs board returns nothing** → confirm the ATS (Greenhouse/Lever/Ashby)
     and the board token in the URL path; otherwise the JSON-LD fallback applies.
   - **Playwright error "Executable doesn't exist"** → `uv run playwright install chromium`.

## Handle rate limits

- **Scraping:** raise `COMPETE_THROTTLE_SECONDS`; the collector also honors any
  `Crawl-delay` in robots.txt (uses the stricter of the two).
- **LLM:** the snapshot-diff gate means only real changes hit the model. Cap a
  run with `compete extract -n N`. Switch provider with `-p groq` / `-p ollama`,
  or `-p mock` for zero cost. Token usage per call is logged in `raw.llm_calls`
  (`compete status` shows the running total).

## Inspect the warehouse

```bash
uv run compete status                  # counts + latest signals + token total
uv run python scripts/inspect_marts.py # mart row counts + samples
cd warehouse/dbt && dbt docs generate && dbt docs serve   # lineage + catalog
```

## Reports & alerts

```bash
uv run compete report          # generate the weekly brief (stored in raw.reports)
uv run compete alert-test      # dry-run an alert (or live if configured + enabled)
```

Enable alerts by setting `COMPETE_ALERTS_ENABLED=true` plus a `SLACK_WEBHOOK_URL`
and/or SMTP_* vars in `.env`.
