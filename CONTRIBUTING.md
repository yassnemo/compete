# Contributing

Thanks for your interest in `compete`! This document covers local setup and the
quality bar for changes.

## Setup

```bash
# Python (uv manages the 3.12 toolchain automatically)
uv sync --extra dev --extra dbt --extra api --extra report
uv run playwright install chromium
cp .env.example .env

# Web
cd web && npm install
```

## Project layout

```
pipeline/    collect · extract · detect · report · storage · transform · cli
warehouse/   dbt project (staging → marts, tests, docs)
api/         FastAPI app
web/         Next.js dashboard
config/      competitors.yaml
docs/        architecture, data model, agents, runbook, deployment, ADRs
scripts/     seed_demo · demo · screenshots · inspect_marts
tests/       pytest suite (LLM mocked)
```

## Quality gates (must pass before merge)

**Python**
```bash
uv run ruff check pipeline tests api scripts
uv run black --check pipeline tests api scripts
uv run pytest
```

**dbt**
```bash
cd warehouse/dbt && dbt build      # builds marts + runs 40 data tests
```

**Web**
```bash
cd web && npm run lint && npm run typecheck && npm run build
```

## Conventions

- **Type hints everywhere** in Python; no `any` in TypeScript.
- The LLM is mocked in tests (`COMPETE_LLM_PROVIDER=mock`) - never call a live
  model from the test suite.
- Keep secrets out of code; everything is env-driven via `.env` / Settings.
- Scraping must stay ethical: public pages only, honor `robots.txt`, throttle,
  honest User-Agent. Don't add login-walled or aggressive collectors.
- New signal types: add to `pipeline/schemas.py::SignalType`, give them styling
  in `web/src/lib/signal-meta.tsx`, and update the `accepted_values` dbt test.
- Architecture decisions go in `docs/adr/` as short ADRs.

## Adding a collector

Implement `collect(competitor_id, url) -> list[RawPage]` (see
`pipeline/collect/static.py`), register it in `pipeline/collect/dispatch.py`,
and add a `SourceType`. Be defensive: never raise on a single fetch failure.
