import type { Metadata } from "next";
import type { ReactNode } from "react";

import { LandingFooter } from "@/components/landing/landing-footer";
import { LandingNav } from "@/components/landing/landing-nav";

export const metadata: Metadata = {
  title: "Technical documentation · compete",
  description:
    "How compete works: collection, LLM extraction, change detection, the DuckDB warehouse, the API, and the frontend. Design decisions and known limitations.",
};

const TOC = [
  { id: "overview", label: "Overview" },
  { id: "architecture", label: "Architecture" },
  { id: "collection", label: "Collection" },
  { id: "extraction", label: "Extraction" },
  { id: "change-detection", label: "Change detection" },
  { id: "warehouse", label: "Warehouse" },
  { id: "api", label: "API" },
  { id: "frontend", label: "Frontend" },
  { id: "reports-alerts", label: "Reports and alerts" },
  { id: "operations", label: "Operations" },
  { id: "limitations", label: "Limitations" },
];

function Section({ id, n, title, children }: { id: string; n: string; title: string; children: ReactNode }) {
  return (
    <section id={id} className="scroll-mt-28 border-t border-border py-10 first:border-t-0 first:pt-0">
      <div className="flex items-baseline gap-3">
        <span className="font-serif text-base italic text-primary">({n})</span>
        <h2 className="text-2xl font-semibold tracking-tight">{title}</h2>
      </div>
      <div className="mt-5 space-y-4 text-[0.95rem] leading-relaxed text-foreground/85">{children}</div>
    </section>
  );
}

function Code({ children }: { children: string }) {
  return (
    <pre className="overflow-x-auto rounded-xl border border-border bg-[hsl(var(--ink))] p-4 text-[0.82rem] leading-relaxed text-[hsl(var(--bone))] scrollbar-thin">
      <code>{children}</code>
    </pre>
  );
}

function K({ children }: { children: ReactNode }) {
  return (
    <code className="rounded bg-secondary px-1.5 py-0.5 font-mono text-[0.85em] text-foreground">
      {children}
    </code>
  );
}

function Table({ head, rows }: { head: string[]; rows: ReactNode[][] }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-border scrollbar-thin">
      <table className="w-full min-w-[36rem] border-collapse text-sm">
        <thead>
          <tr className="border-b border-border bg-secondary/50 text-left">
            {head.map((h) => (
              <th key={h} className="px-4 py-2.5 font-medium text-muted-foreground">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-b border-border last:border-b-0">
              {r.map((c, j) => (
                <td key={j} className="px-4 py-2.5 align-top">
                  {c}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function DocsPage() {
  return (
    <div className="relative min-h-screen bg-background text-foreground">
      <LandingNav />

      <main className="mx-auto max-w-[1640px] px-4 pb-20 pt-28 sm:px-6 sm:pt-32">
        {/* Page header */}
        <header className="max-w-3xl">
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">
            Documentation
          </p>
          <h1 className="mt-3 text-4xl font-semibold tracking-tight sm:text-5xl">
            How compete works
          </h1>
          <p className="mt-4 text-muted-foreground">
            This page documents the system as built: what each stage does, the decisions behind
            it, and where it falls short. It is written for engineers who want to evaluate or
            extend the project.
          </p>
          <div className="mt-6 flex flex-wrap gap-x-6 gap-y-2 text-sm text-muted-foreground">
            <span>
              Stack: <span className="text-foreground">Python 3.12, DuckDB, dbt, FastAPI, Next.js 14</span>
            </span>
            <span>
              Status: <span className="text-foreground">working end to end, demo data seeded</span>
            </span>
          </div>
        </header>

        <div className="mt-12 grid grid-cols-1 gap-12 lg:grid-cols-[220px,minmax(0,1fr)]">
          {/* TOC */}
          <nav aria-label="Table of contents" className="hidden lg:block">
            <div className="sticky top-24">
              <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                Contents
              </p>
              <ul className="mt-4 space-y-1 border-l border-border">
                {TOC.map((t, i) => (
                  <li key={t.id}>
                    <a
                      href={`#${t.id}`}
                      className="block border-l-2 border-transparent py-1 pl-4 text-sm text-muted-foreground transition-colors hover:border-primary hover:text-foreground"
                    >
                      <span className="mr-2 font-mono text-xs text-muted-foreground/60">
                        {String(i + 1).padStart(2, "0")}
                      </span>
                      {t.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </nav>

          {/* Content */}
          <article className="max-w-3xl">
            <Section id="overview" n="01" title="Overview">
              <p>
                compete monitors a configurable list of companies and turns changes on their
                public web presence into structured records called signals. A signal has a type
                (pricing change, product launch, job posting, and so on), a significance score
                from 1 to 5, a summary, and a link back to the source page.
              </p>
              <p>
                The system is a batch pipeline, not a streaming one. Each run collects pages,
                detects which ones actually changed, sends only the changed content to an LLM for
                extraction, stores the results in a local DuckDB file, and rebuilds a set of dbt
                models that the dashboard reads through a FastAPI service.
              </p>
              <p>
                Everything runs from files on disk. There is no managed database, no queue, and
                no cloud dependency. A weekly GitHub Actions cron is enough to keep it current,
                and the whole thing can run on a laptop.
              </p>
            </Section>

            <Section id="architecture" n="02" title="Architecture">
              <Code>{`collect            extract              transform           serve
┌──────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────┐
│ httpx    │     │ change gate  │     │ DuckDB raw  │     │ FastAPI  │
│ feedparser│ →  │ LLM (instructor) │ → │ dbt staging │  →  │ Next.js  │
│ Playwright│     │ + validation │     │ dbt marts   │     │ dashboard│
│ ATS APIs │     │ retry        │     │             │     │          │
└──────────┘     └──────────────┘     └─────────────┘     └──────────┘
      ↓                  ↓
 Parquet landing    raw.llm_calls
 zone (partitioned) (cost log)`}</Code>
              <p>
                The pipeline stages are decoupled by the database: collection writes raw pages,
                extraction reads pending pages and writes signals, dbt reads signals and builds
                marts, and the API only reads marts and raw tables. Any stage can be re-run
                independently, and a failed run can be retried without touching the others.
              </p>
              <p>
                A single Typer CLI exposes each stage (<K>compete collect</K>,{" "}
                <K>compete extract</K>, <K>compete report</K>) plus <K>compete run-all</K>, which
                chains sync, collect, extract, dbt build, and report generation.
              </p>
            </Section>

            <Section id="collection" n="03" title="Collection">
              <p>
                Each tracked URL declares a source type in <K>competitors.yaml</K>, and a registry
                dispatches it to the right collector. All four collectors implement the same
                interface and return a list of raw page records.
              </p>
              <Table
                head={["Collector", "Used for", "Implementation"]}
                rows={[
                  [
                    <K key="s">static</K>,
                    "Plain HTML pages (pricing, about, news indexes)",
                    "httpx for fetching, trafilatura for boilerplate removal and main-content extraction",
                  ],
                  [
                    <K key="r">rss</K>,
                    "Blogs and changelogs that publish feeds",
                    "feedparser; each entry becomes its own page record",
                  ],
                  [
                    <K key="d">dynamic</K>,
                    "Pages that require JavaScript to render",
                    "Playwright with headless Chromium, then the same trafilatura pass",
                  ],
                  [
                    <K key="j">jobs</K>,
                    "Careers pages",
                    "Greenhouse, Lever, and Ashby public JSON APIs, with a JSON-LD JobPosting fallback for everything else",
                  ],
                ]}
              />
              <p>
                The collectors respect <K>robots.txt</K>, including <K>Crawl-delay</K>, and apply
                per-host throttling with retries and exponential backoff. Pages are stored twice:
                in the DuckDB <K>raw.raw_pages</K> table for the pipeline, and as Parquet files
                partitioned by competitor and date, which serve as a replayable landing zone if
                the database ever needs to be rebuilt.
              </p>
              <p>
                A full collection run across the five seeded companies fetches a few hundred
                pages. The jobs collector accounts for most of that volume because each posting
                is a separate record.
              </p>
            </Section>

            <Section id="extraction" n="04" title="Extraction">
              <p>
                Extraction is the only place the system calls an LLM, and the design treats the
                model as an unreliable component. The client is provider agnostic: Gemini Flash
                is the default, with Groq and Ollama as alternatives and a deterministic mock
                provider used by the test suite and for offline development. Switching providers
                is one environment variable.
              </p>
              <p>
                Responses are parsed into Pydantic models through the instructor library. If
                validation fails, the request is retried exactly once with the validation errors
                appended to the prompt. If it fails again, the page is marked failed and the run
                continues. There is no silent fallback that fabricates a signal.
              </p>
              <p>
                Every call logs its token counts and estimated cost to <K>raw.llm_calls</K>, so
                the cost of a run is a query away rather than a guess. A full extraction pass on
                the seeded dataset stays comfortably inside Gemini&apos;s free tier.
              </p>
            </Section>

            <Section id="change-detection" n="05" title="Change detection">
              <p>
                Most pages do not change between runs, and sending unchanged content to an LLM is
                wasted money. Before extraction, each page goes through a two-stage gate:
              </p>
              <p>
                First, an exact content hash comparison against the previous snapshot. If the
                hash matches, the page is skipped. Second, for pages that did change, an
                embedding cosine similarity check filters out trivial edits (dates, footers,
                rotating links). Only pages below the similarity threshold proceed to the LLM.
              </p>
              <p>
                The default embedding backend is a hashing vectorizer with no model download and
                no external calls. MiniLM and Gemini embeddings are available behind the same
                interface when better semantic accuracy is worth the dependency.
              </p>
              <p>
                Idempotency is enforced with a uniqueness constraint on the URL and source hash
                pair, so re-running extraction on the same data produces zero new signals rather
                than duplicates. This was verified by running the pipeline twice over identical
                input.
              </p>
            </Section>

            <Section id="warehouse" n="06" title="Warehouse">
              <p>
                Storage is a single DuckDB file. Raw tables hold pages, signals, detected
                changes, LLM call logs, and reports. dbt builds staging views on top of raw, then
                six marts that the API queries:
              </p>
              <Table
                head={["Mart", "What it answers"]}
                rows={[
                  [<K key="1">dim_competitors</K>, "Who is tracked, with signal counts and metadata"],
                  [
                    <K key="2">fct_changes</K>,
                    "Every detected change with a weighted significance score",
                  ],
                  [<K key="3">fct_hiring</K>, "Open roles parsed from job postings, by location and team"],
                  [
                    <K key="4">fct_pricing_history</K>,
                    "Plan prices over time, extracted heuristically from pricing pages",
                  ],
                  [<K key="5">agg_weekly_competitor</K>, "Weekly activity rollups per competitor"],
                  [
                    <K key="6">fct_signal_duplicates</K>,
                    "Near-duplicate signals found via embedding cosine similarity at or above 0.95",
                  ],
                ]}
              />
              <p>
                The dbt project carries schema tests (not null, accepted values, relationships)
                on both staging and marts; the full build runs about fifty checks. Choosing
                DuckDB over Postgres was deliberate: the data is small, the access pattern is
                analytical, a file is trivially portable, and DuckDB&apos;s vector functions
                (<K>list_cosine_similarity</K>) made the dedup mart a plain SQL model instead of
                a Python job.
              </p>
            </Section>

            <Section id="api" n="07" title="API">
              <p>
                A FastAPI service reads the warehouse and exposes it as JSON. The interesting
                parts are less the endpoints than the edge handling:
              </p>
              <p>
                DuckDB allows one writer, so the API holds a read connection and serializes any
                write through a lock. Endpoints that read marts degrade gracefully when marts
                have not been built yet (fresh clone, no dbt run) instead of returning 500s. List
                endpoints share a generic <K>Page[T]</K> envelope with limit and offset, and
                errors use one envelope shape everywhere.
              </p>
              <Table
                head={["Router", "Endpoints"]}
                rows={[
                  ["competitors", "CRUD for tracked companies"],
                  ["signals, changes", "Filterable, paginated lists (competitor, type, significance, date)"],
                  ["analytics", "Pricing history, hiring, content cadence, stats overview"],
                  ["reports", "List, read, and download weekly briefs as PDF"],
                  ["pipeline", "Trigger a collection run as a background task"],
                ]}
              />
              <p>
                Interactive docs are served at <K>/docs</K> by FastAPI. The Next.js app proxies{" "}
                <K>/api/*</K> to the service through a rewrite, so the frontend never hardcodes
                the API origin.
              </p>
            </Section>

            <Section id="frontend" n="08" title="Frontend">
              <p>
                The dashboard is Next.js 14 (App Router) with TypeScript. UI primitives (button,
                card, dialog, select, tabs) are hand-built in the shadcn style on Radix, charts
                are Tremor, and server state goes through TanStack Query with typed fetch
                wrappers. The marketing site and this documentation page live in the same app
                and share one design system: warm paper and ink surfaces, a single lime accent,
                Space Grotesk for UI text, and a serif italic for editorial accents.
              </p>
              <p>
                Pages are deliberately boring in structure: overview, per-competitor detail,
                a filterable changes table, reports with a PDF download, and settings. Every
                data view has explicit loading, empty, and error states, which is most of what
                separates a dashboard that feels finished from one that does not.
              </p>
              <p>
                Animation is used twice on the marketing side (GSAP scroll reveals, Framer Motion
                in the hero) and once in the app (a short route transition). Decorative motion is
                disabled when the user requests reduced motion.
              </p>
            </Section>

            <Section id="reports-alerts" n="09" title="Reports and alerts">
              <p>
                A weekly brief is generated from the marts: top changes by weighted significance,
                per-competitor activity, and pricing movements. The body of the report is
                deterministic. When a real LLM provider is configured, an executive summary is
                generated and prepended; without one, a template summary is used, so report
                generation never depends on an API key.
              </p>
              <p>
                PDFs are rendered with fpdf2, which is pure Python. The first implementation used
                WeasyPrint, which produces nicer output but drags in GTK system dependencies on
                Windows; that tradeoff was not worth it for a portfolio project that should clone
                and run anywhere.
              </p>
              <p>
                Alerts fire when a signal&apos;s weighted significance crosses a threshold,
                through a Slack webhook or SMTP email. Delivery is disabled by default and the
                alert path logs what it would have sent when no channel is configured, which
                makes the behavior testable without secrets.
              </p>
            </Section>

            <Section id="operations" n="10" title="Operations">
              <p>Local setup, from a fresh clone:</p>
              <Code>{`uv sync --extra dev --extra dbt --extra api   # Python env + deps
uv run compete init-db                        # create the DuckDB schema
uv run python scripts/seed_demo.py --build    # demo data + dbt build
uv run compete-api                            # FastAPI on :8000
cd web && npm install && npm run dev          # dashboard on :3000`}</Code>
              <p>
                Tooling is uv for Python environments, ruff and black for linting and formatting,
                pytest for the Python suite (collectors, extraction, change detection, API), and
                ESLint plus a strict TypeScript config on the frontend. A GitHub Actions workflow
                runs the pipeline weekly and uploads the warehouse file as an artifact.
              </p>
              <p>
                Running cost is zero by design: GitHub Actions free tier for compute, a file for
                storage, and an LLM free tier for extraction. The deployment doc in the repo
                walks through the paid options if the project ever needed them.
              </p>
            </Section>

            <Section id="limitations" n="11" title="Limitations">
              <p>
                Things that are honest to call out, in rough order of how much they would matter
                in production:
              </p>
              <p>
                Pricing extraction is heuristic. It works on conventional pricing pages and
                produces sparse history elsewhere; a production system would want per-site
                adapters or a vision model reading rendered pages.
              </p>
              <p>
                The API has no authentication. It is built to run on localhost or behind a
                private proxy, and adding auth was out of scope for a single-user demo.
              </p>
              <p>
                DuckDB&apos;s single-writer model is fine for a batch pipeline plus a read-mostly
                API, but it would not survive multiple concurrent writers. The Parquet landing
                zone is the escape hatch: the warehouse can be rebuilt from it into any engine.
              </p>
              <p>
                Significance scoring is a weighted formula over type and LLM-assigned importance,
                tuned by eye against the seeded dataset. It has no feedback loop; signals you
                ignore do not teach it anything yet.
              </p>
              <p>
                The demo dataset is curated. The collectors are real and run against live sites,
                but the dashboard you are looking at is seeded so that it demonstrates every
                feature without waiting a month for history to accumulate.
              </p>
            </Section>
          </article>
        </div>
      </main>

      <LandingFooter />
    </div>
  );
}
