"""Phase 1 collector tests - offline (no network)."""

from __future__ import annotations

from pathlib import Path

import duckdb
import feedparser
from pipeline.collect.dispatch import CollectorRegistry
from pipeline.collect.dynamic import DynamicCollector
from pipeline.collect.jobs import JobsCollector, parse_jsonld_jobs
from pipeline.collect.rss import RSSCollector, _entry_text
from pipeline.collect.static import StaticCollector
from pipeline.schemas import RawPage, SourceType, utcnow
from pipeline.storage.parquet_store import write_raw_pages

SAMPLE_RSS = """<?xml version="1.0"?>
<rss version="2.0"><channel>
  <title>Acme Blog</title>
  <item>
    <title>We launched Widget 2.0</title>
    <link>https://acme.com/blog/widget-2</link>
    <description>Widget 2.0 is here with faster sync.</description>
    <pubDate>Tue, 03 Jun 2025 09:00:00 GMT</pubDate>
  </item>
</channel></rss>"""

SAMPLE_JOBS_HTML = """
<html><head>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"JobPosting",
 "title":"Staff Engineer","url":"https://acme.com/jobs/staff-eng",
 "description":"<p>Build <b>things</b>.</p>",
 "jobLocation":{"@type":"Place","address":{"@type":"PostalAddress","addressLocality":"Remote"}}}
</script>
</head><body>careers</body></html>
"""


def test_rss_entry_text() -> None:
    feed = feedparser.parse(SAMPLE_RSS)
    assert feed.entries
    text = _entry_text(feed.entries[0])
    assert "Widget 2.0" in text


def test_jsonld_jobs_parsing() -> None:
    jobs = parse_jsonld_jobs(SAMPLE_JOBS_HTML, base_url="https://acme.com/careers")
    assert len(jobs) == 1
    job = jobs[0]
    assert job.title == "Staff Engineer"
    assert job.location == "Remote"
    assert "Build things" in (job.body or "")  # HTML stripped
    assert job.url == "https://acme.com/jobs/staff-eng"


def test_dispatch_routes_to_correct_collector() -> None:
    reg = CollectorRegistry()
    assert isinstance(reg.get(SourceType.STATIC), StaticCollector)
    assert isinstance(reg.get(SourceType.DYNAMIC), DynamicCollector)
    assert isinstance(reg.get(SourceType.RSS), RSSCollector)
    assert isinstance(reg.get(SourceType.JOBS), JobsCollector)
    # cached (same instance on second call)
    assert reg.get(SourceType.STATIC) is reg.get(SourceType.STATIC)


def test_parquet_roundtrip(tmp_path: Path) -> None:
    pages = [
        RawPage(
            id=f"id{i}",
            competitor_id="acme",
            url=f"https://acme.com/{i}",
            source_type=SourceType.RSS,
            raw_html="<p>hi</p>",
            clean_text="hello world",
            content_hash=f"h{i}",
            http_status=200,
            fetched_at=utcnow(),
        )
        for i in range(3)
    ]
    root = write_raw_pages(pages, tmp_path)
    assert root is not None and root.exists()

    # DuckDB should read the partitioned dataset back.
    con = duckdb.connect()
    glob = str(root / "**" / "*.parquet").replace("\\", "/")
    n = con.execute(
        "SELECT count(*) FROM read_parquet(?, hive_partitioning=true)", [glob]
    ).fetchone()[0]
    assert n == 3
    con.close()


def test_write_raw_pages_empty_is_noop(tmp_path: Path) -> None:
    assert write_raw_pages([], tmp_path) is None
