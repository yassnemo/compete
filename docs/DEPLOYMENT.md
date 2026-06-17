# Deployment

`compete` has three deployable pieces: the **scheduled pipeline**, the **API**,
and the **web dashboard**. All can run on free tiers.

## Topology

```
GitHub Actions cron ──> compete run-all ──> data/compete.duckdb (artifact)
                                                   │
        Oracle Free VM / Fly.io  ──> compete-api (FastAPI, reads the .duckdb)
                                                   │
                       Vercel ──> Next.js dashboard ──(/api proxy)──> API
```

DuckDB is a single file, which shapes deployment: the pipeline writes it; the
API reads it. Pick one of the patterns below.

## 1. Scheduled pipeline - GitHub Actions (free)

`.github/workflows/pipeline.yml` runs `compete run-all` on a weekly cron (and on
manual dispatch). It installs uv + Chromium, runs the pipeline, generates dbt
docs, and uploads `data/compete.duckdb` + reports as a build artifact.

**Secrets** (repo → Settings → Secrets → Actions):

| Secret | Purpose |
|--------|---------|
| `GOOGLE_API_KEY` | Gemini extraction (default provider) |
| `GROQ_API_KEY` | optional, if using Groq |
| `SLACK_WEBHOOK_URL` | optional; presence enables alerts |

To **persist** the warehouse between runs (instead of artifacts), either commit
the `.duckdb` back to the repo on a data branch, push it to object storage
(e.g. Cloudflare R2 free tier), or point the pipeline at a hosted DB (below).

## 2. API - Oracle Cloud Always Free VM (or Fly.io)

The API needs the `.duckdb` file on disk. On an Always-Free Ampere VM:

```bash
git clone <repo> && cd compete
uv sync --extra api
# fetch the latest warehouse artifact (or run the pipeline on the VM)
COMPETE_API_HOST=0.0.0.0 uv run compete-api
```

Run it under `systemd` or `pm2`, front it with Caddy/Nginx for TLS, and have the
pipeline (cron on the same VM, or an artifact download) refresh the `.duckdb`.
Set `COMPETE_CORS_ORIGINS` to your Vercel URL.

## 3. Web - Vercel (free)

```
Root directory:   web
Framework preset: Next.js
Env:              API_PROXY_TARGET = https://<your-api-host>
```

The app calls `/api/*`, which `next.config.mjs` rewrites to `API_PROXY_TARGET`,
so the browser stays same-origin (no CORS in the browser). For a pure-static
showcase, run `scripts/seed_demo.py --build` and point the API at the seeded
warehouse.

## Optional: hosted operational store (Supabase)

The brief's default is fully file-based (DuckDB). If you want a hosted CRUD store
for competitors/settings, provision a free Supabase Postgres and mirror
`raw.competitors` there; the analytical marts stay in DuckDB. This is documented
as optional and not wired by default (see ADR 0001).

## Environment variables

All config is env-driven (`.env` locally, secrets in CI/hosting). See
`.env.example` for the full list: paths, `COMPETE_LLM_PROVIDER` + keys,
embeddings, collection throttle/robots, alerts, and API host/port/CORS.

## Free-tier cost summary

| Component | Service | Cost |
|-----------|---------|------|
| Pipeline schedule | GitHub Actions | Free (2,000 min/mo) |
| LLM extraction | Gemini Flash / Groq free tier, or Ollama local / mock | $0 |
| Embeddings | local hashing (default) or local MiniLM | $0 |
| Warehouse | DuckDB + Parquet (file) | $0 |
| API host | Oracle Always Free VM / Fly.io free | $0 |
| Dashboard | Vercel Hobby | $0 |
| Alerts | Slack webhook / SMTP | $0 |

**Total: $0** with the default/local providers; only paid if you exceed an LLM
free tier.
