"""Seed the warehouse with curated, realistic demo data.

Makes the API and dashboard fully demoable without any API key or pipeline run.
Populates the raw layer (competitors, signals, changes, jobs snapshots, llm
calls, reports) with hand-authored data, then (optionally) runs ``dbt build`` to
materialize the marts.

Usage:
    uv run python scripts/seed_demo.py            # seed raw only
    uv run python scripts/seed_demo.py --build    # seed + dbt build
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import UTC, datetime, timedelta

from pipeline.config import REPO_ROOT, get_settings
from pipeline.extract.embeddings import HashingEmbedder
from pipeline.logging_setup import get_logger
from pipeline.schemas import RawPage, SourceType
from pipeline.storage.duckdb_store import Warehouse

log = get_logger("seed")
EMB = HashingEmbedder(256)
NOW = datetime.now(UTC)


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60]


def _hash(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:24]


def _ago(days: float) -> datetime:
    return NOW - timedelta(days=days)


COMPETITORS = [
    ("anthropic", "Anthropic", "anthropic.com", "AI / LLM", 1),
    ("openai", "OpenAI", "openai.com", "AI / LLM", 1),
    ("google-deepmind", "Google DeepMind", "deepmind.google", "AI / LLM", 1),
    ("mistral", "Mistral AI", "mistral.ai", "AI / LLM", 2),
    ("cohere", "Cohere", "cohere.com", "AI / Enterprise NLP", 2),
]

TRACKED = {
    "anthropic": [
        ("https://www.anthropic.com/news", "static", "press_release"),
        ("https://www.anthropic.com/pricing", "static", "pricing_change"),
    ],
    "openai": [("https://openai.com/news", "dynamic", "product_launch")],
    "google-deepmind": [("https://deepmind.google/discover/blog/", "static", "blog_post")],
    "mistral": [("https://mistral.ai/news", "dynamic", "product_launch")],
    "cohere": [("https://cohere.com/blog", "static", "blog_post")],
}

# (days_ago, signal_type, title, summary, significance)
CONTENT = {
    "anthropic": [
        (
            3,
            "product_launch",
            "Claude Opus 4.8 released",
            "Anthropic launched Claude Opus 4.8 with stronger coding and agentic performance. Available today via API and Claude apps.",
            5,
        ),
        (
            9,
            "press_release",
            "Enterprise expansion in EMEA",
            "Anthropic announced new London and Dublin offices to serve enterprise demand across Europe.",
            3,
        ),
        (
            16,
            "leadership_change",
            "New VP of Sales hired",
            "Anthropic appointed a new VP of Sales to lead its go-to-market expansion.",
            4,
        ),
        (
            24,
            "blog_post",
            "Interpretability research update",
            "A research post detailing progress on feature steering in large models.",
            2,
        ),
        (
            38,
            "funding_news",
            "Series F at $60B valuation",
            "Anthropic raised a Series F round reportedly valuing the company around $60B.",
            5,
        ),
    ],
    "openai": [
        (
            2,
            "product_launch",
            "GPT-5.2 Turbo announced",
            "OpenAI introduced GPT-5.2 Turbo with a larger context window and lower latency.",
            5,
        ),
        (
            12,
            "pricing_change",
            "API price cut for flagship model",
            "OpenAI reduced flagship API pricing, with the Pro plan now $18/mo for individuals.",
            4,
        ),
        (
            20,
            "leadership_change",
            "CFO transition",
            "OpenAI announced a CFO transition as it scales commercial operations.",
            4,
        ),
        (
            33,
            "blog_post",
            "Safety evaluations framework",
            "A blog post outlining an updated safety evaluation framework.",
            2,
        ),
    ],
    "google-deepmind": [
        (
            5,
            "product_launch",
            "Gemini 3 Flash general availability",
            "Google DeepMind made Gemini 3 Flash generally available with improved multimodal reasoning.",
            5,
        ),
        (
            18,
            "blog_post",
            "AlphaProof milestone",
            "A research blog on new math-reasoning benchmarks results.",
            3,
        ),
        (
            29,
            "press_release",
            "Cloud partnership expansion",
            "DeepMind models expanded across additional Google Cloud regions.",
            3,
        ),
    ],
    "mistral": [
        (
            4,
            "product_launch",
            "Mistral Large 3 launched",
            "Mistral released Mistral Large 3, a unified agent for long-horizon productivity tasks.",
            5,
        ),
        (
            14,
            "funding_news",
            "New financing round",
            "Mistral AI closed a new financing round to fund European data-center capacity.",
            4,
        ),
        (
            27,
            "blog_post",
            "Open-weights model update",
            "Mistral published updated open-weights checkpoints for the community.",
            3,
        ),
    ],
    "cohere": [
        (
            6,
            "product_launch",
            "Command R+ refresh",
            "Cohere shipped a Command R+ refresh focused on enterprise RAG accuracy.",
            4,
        ),
        (
            21,
            "press_release",
            "SOC 2 Type II + new compliance",
            "Cohere announced expanded compliance certifications for regulated industries.",
            3,
        ),
        (
            35,
            "blog_post",
            "Multilingual embeddings",
            "A post on improved multilingual embedding quality.",
            2,
        ),
    ],
}

# (days_ago, plan, price) -> emitted as pricing_change signals (chart source)
PRICING = {
    "anthropic": [(60, "Pro", 20), (30, "Pro", 20), (8, "Team", 30), (8, "Max", 100)],
    "openai": [(55, "Plus", 20), (25, "Plus", 20), (12, "Pro", 18), (12, "Team", 25)],
    "google-deepmind": [(40, "Pro", 20), (10, "Pro", 22)],
    "mistral": [(45, "Pro", 15), (15, "Pro", 15), (15, "Team", 25)],
    "cohere": [(50, "Starter", 0), (20, "Scale", 50)],
}

# (role, location, days_ago)
JOBS = {
    "anthropic": [
        ("Staff Software Engineer, Inference", "San Francisco, CA", 2),
        ("Product Manager, Claude Code", "San Francisco, CA | Seattle, WA", 6),
        ("Research Scientist, Alignment", "London, UK", 11),
        ("Enterprise Account Executive", "New York City, NY", 15),
    ],
    "openai": [
        ("Member of Technical Staff, Scaling", "San Francisco, CA", 3),
        ("Solutions Architect", "Remote, US", 9),
        ("Recruiter, Technical", "San Francisco, CA", 17),
    ],
    "google-deepmind": [
        ("Research Engineer, Gemini", "Mountain View, CA", 4),
        ("Program Manager, Responsible AI", "London, UK", 13),
    ],
    "mistral": [
        ("Infrastructure Engineer", "Paris, France", 5),
        ("Developer Relations Engineer", "Remote, EU", 19),
    ],
    "cohere": [
        ("ML Engineer, Retrieval", "Toronto, Canada", 7),
        ("Enterprise Solutions Engineer", "Remote, US", 22),
    ],
}


def _wipe(wh: Warehouse) -> None:
    for table in ("signals", "changes", "llm_calls", "reports", "raw_pages", "competitors"):
        wh.conn.execute(f"DELETE FROM raw.{table}")


def _store_signal_and_change(
    wh: Warehouse,
    comp_id: str,
    domain: str,
    when: datetime,
    signal_type: str,
    title: str,
    summary: str,
    significance: int,
) -> int:
    url = f"https://{domain}/news/{_slug(title)}"
    source_hash = _hash(f"{comp_id}:{title}:{when.isoformat()}")
    sid = _hash(f"{url}:{source_hash}")
    wh.upsert_signal(
        signal_id=sid,
        competitor_id=comp_id,
        url=url,
        signal_type=signal_type,
        title=title,
        summary=summary,
        entities_json=json.dumps(_entities(title)),
        significance=significance,
        confidence=0.85,
        embedding=EMB.embed_one(f"{title} {summary}"),
        source_hash=source_hash,
        model="seed",
        extracted_at=when,
    )
    wh.insert_change(
        change_id=f"chg-{sid}",
        competitor_id=comp_id,
        url=url,
        signal_type=signal_type,
        change_type="new",
        summary=summary,
        significance_score=significance,
        prev_hash=None,
        new_hash=source_hash,
        detected_at=when,
    )
    return significance


def _entities(title: str) -> list[str]:
    return re.findall(r"[A-Z][A-Za-z0-9.+]+(?:\s[A-Z0-9][A-Za-z0-9.+]*){0,2}", title)[:4]


def seed(wh: Warehouse) -> dict[str, int]:
    _wipe(wh)
    counts = {"competitors": 0, "signals": 0, "changes": 0, "jobs": 0, "reports": 0}

    for cid, name, domain, industry, tier in COMPETITORS:
        tracked = [
            {"url": u, "source_type": st, "signal_hint": sh} for u, st, sh in TRACKED.get(cid, [])
        ]
        wh.upsert_competitor(cid, name, domain, industry, tier, json.dumps(tracked))
        counts["competitors"] += 1

        for days, st, title, summary, sig in CONTENT.get(cid, []):
            _store_signal_and_change(wh, cid, domain, _ago(days), st, title, summary, sig)
            counts["signals"] += 1
            counts["changes"] += 1

        for days, plan, price in PRICING.get(cid, []):
            title = f"{plan} plan pricing update"
            summary = (
                f"The {plan} plan is now ${price}/mo." if price else f"The {plan} plan is now free."
            )
            _store_signal_and_change(
                wh, cid, domain, _ago(days), "pricing_change", title, summary, 3
            )
            counts["signals"] += 1
            counts["changes"] += 1

        for role, location, days in JOBS.get(cid, []):
            when = _ago(days)
            body = f"{role} ({location})\n\nWe are hiring a {role} based in {location}."
            chash = _hash(f"{cid}:{role}:{location}")
            wh.upsert_raw_page(
                RawPage(
                    id=_hash(f"jobs:{cid}:{role}"),
                    competitor_id=cid,
                    url=f"https://boards.{domain}/jobs/{_slug(role)}",
                    source_type=SourceType.JOBS,
                    raw_html=body,
                    clean_text=body,
                    http_status=200,
                    content_hash=chash,
                    fetched_at=when,
                )
            )
            counts["jobs"] += 1

    # A few LLM call logs for cost display.
    for i in range(12):
        wh.log_llm_call(
            call_id=f"seed-call-{i}",
            ts=_ago(i),
            provider="gemini",
            model="gemini-1.5-flash",
            url="https://example.com",
            prompt_tokens=1200,
            completion_tokens=180,
            total_tokens=1380,
            latency_ms=900,
            ok=True,
            error=None,
        )

    # Two demo weekly reports.
    for wk, title in [(7, "Weekly Competitive Brief"), (14, "Weekly Competitive Brief")]:
        week_start = (_ago(wk)).date()
        body = (
            f"# {title} - week of {week_start}\n\n"
            "## Executive summary\n"
            "Major model launches from Anthropic and OpenAI dominated the week, alongside "
            "pricing movement and continued hiring in inference and GTM roles.\n\n"
            "## Top changes\n"
            "1. **Anthropic - Claude Opus 4.8 released** (significance 5)\n"
            "2. **OpenAI - GPT-5.2 Turbo announced** (significance 5)\n"
            "3. **OpenAI - API price cut**, Pro now $18/mo (significance 4)\n\n"
            "## What to watch\n"
            "- European data-center buildout (Mistral financing).\n"
            "- Enterprise compliance positioning (Cohere).\n"
        )
        wh.upsert_report(
            report_id=f"report-{week_start}",
            title=f"{title} - {week_start}",
            week_start=week_start,
            summary="Model launches from Anthropic & OpenAI; pricing moves; steady hiring.",
            body_md=body,
            created_at=_ago(wk - 0.2),
        )
        counts["reports"] += 1

    return counts


def run_dbt_build() -> bool:
    import os

    from dbt.cli.main import dbtRunner

    os.environ["COMPETE_DUCKDB_PATH"] = str(get_settings().duckdb_path)
    proj = str(REPO_ROOT / "warehouse" / "dbt")
    res = dbtRunner().invoke(["build", "--project-dir", proj, "--profiles-dir", proj])
    return bool(res.success)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo data into the warehouse.")
    parser.add_argument("--build", action="store_true", help="Run dbt build after seeding.")
    args = parser.parse_args()

    settings = get_settings()
    settings.ensure_dirs()
    wh = Warehouse.from_settings(settings)
    counts = seed(wh)
    wh.close()
    log.info("seeded: %s", counts)
    print("Seeded demo data:", counts)

    if args.build:
        ok = run_dbt_build()
        print("dbt build:", "OK" if ok else "FAILED")
        if not ok:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
