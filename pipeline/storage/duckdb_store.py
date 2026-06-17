"""DuckDB warehouse access layer.

DuckDB is a file-based analytical database - no server. This module owns the
connection, the raw-layer schema bootstrap, and the small set of typed
read/write helpers the rest of the pipeline uses. dbt (Phase 3) builds the
staging/mart layers on top of the same file.
"""

from __future__ import annotations

import contextlib
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import duckdb

from pipeline.config import Settings, get_settings
from pipeline.logging_setup import get_logger
from pipeline.schemas import RawPage

log = get_logger(__name__)

# Raw layer - owned by the pipeline (dbt reads from here, never writes).
_SCHEMA_SQL = """
CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.raw_pages (
    id            VARCHAR PRIMARY KEY,
    competitor_id VARCHAR NOT NULL,
    url           VARCHAR NOT NULL,
    source_type   VARCHAR NOT NULL,
    raw_html      VARCHAR,
    clean_text    VARCHAR,
    http_status   INTEGER,
    content_hash  VARCHAR NOT NULL,
    fetched_at    TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_raw_pages_competitor ON raw.raw_pages (competitor_id);
CREATE INDEX IF NOT EXISTS idx_raw_pages_url ON raw.raw_pages (url);

-- Competitors mirror of config (operational CRUD target for the API).
CREATE TABLE IF NOT EXISTS raw.competitors (
    competitor_id VARCHAR PRIMARY KEY,
    name          VARCHAR NOT NULL,
    domain        VARCHAR,
    industry      VARCHAR,
    tier          INTEGER DEFAULT 2,
    tracked_urls  JSON,
    created_at    TIMESTAMPTZ DEFAULT now(),
    updated_at    TIMESTAMPTZ DEFAULT now()
);

-- Extracted signals (LLM output + embedding). dbt's stg_signals reads this.
CREATE TABLE IF NOT EXISTS raw.signals (
    id            VARCHAR PRIMARY KEY,   -- hash(url, source_hash)
    competitor_id VARCHAR NOT NULL,
    url           VARCHAR,
    signal_type   VARCHAR NOT NULL,
    title         VARCHAR,
    summary       VARCHAR,
    entities      JSON,
    significance  INTEGER,
    confidence    DOUBLE,
    embedding     FLOAT[],
    source_hash   VARCHAR NOT NULL,
    model         VARCHAR,
    extracted_at  TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_signals_competitor ON raw.signals (competitor_id);

-- Detected changes (snapshot diff outcome).
CREATE TABLE IF NOT EXISTS raw.changes (
    change_id          VARCHAR PRIMARY KEY,
    competitor_id      VARCHAR NOT NULL,
    url                VARCHAR,
    signal_type        VARCHAR,
    change_type        VARCHAR NOT NULL,   -- new | updated | removed
    summary            VARCHAR,
    significance_score INTEGER,
    prev_hash          VARCHAR,
    new_hash           VARCHAR,
    detected_at        TIMESTAMPTZ NOT NULL
);

-- LLM call log for cost tracking.
CREATE TABLE IF NOT EXISTS raw.llm_calls (
    id                VARCHAR PRIMARY KEY,
    ts                TIMESTAMPTZ NOT NULL,
    provider          VARCHAR,
    model             VARCHAR,
    url               VARCHAR,
    prompt_tokens     INTEGER,
    completion_tokens INTEGER,
    total_tokens      INTEGER,
    latency_ms        INTEGER,
    ok                BOOLEAN,
    error             VARCHAR
);

-- Generated weekly reports (markdown brief + exec summary).
CREATE TABLE IF NOT EXISTS raw.reports (
    id          VARCHAR PRIMARY KEY,
    title       VARCHAR NOT NULL,
    week_start  DATE,
    summary     VARCHAR,
    body_md     VARCHAR,
    created_at  TIMESTAMPTZ NOT NULL
);
"""


class Warehouse:
    """Thin wrapper around a DuckDB connection with schema bootstrap."""

    def __init__(self, db_path: Path | str, *, read_only: bool = False) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._read_only = read_only
        self.conn = duckdb.connect(str(self.db_path), read_only=read_only)
        if not read_only:
            self.bootstrap()

    @classmethod
    def from_settings(
        cls, settings: Settings | None = None, *, read_only: bool = False
    ) -> Warehouse:
        s = settings or get_settings()
        return cls(s.duckdb_path, read_only=read_only)

    def bootstrap(self) -> None:
        """Create the raw-layer schema if absent (idempotent)."""
        self.conn.execute(_SCHEMA_SQL)

    # ---------------------------- writes ---------------------------------- #
    def upsert_raw_page(self, page: RawPage) -> None:
        """Insert or replace a fetched page snapshot."""
        self.conn.execute(
            """
            INSERT OR REPLACE INTO raw.raw_pages
                (id, competitor_id, url, source_type, raw_html, clean_text,
                 http_status, content_hash, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                page.id,
                page.competitor_id,
                page.url,
                page.source_type.value,
                page.raw_html,
                page.clean_text,
                page.http_status,
                page.content_hash,
                page.fetched_at,
            ],
        )

    def upsert_competitor(
        self,
        competitor_id: str,
        name: str,
        domain: str | None,
        industry: str | None,
        tier: int,
        tracked_urls_json: str,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO raw.competitors
                (competitor_id, name, domain, industry, tier, tracked_urls, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, now())
            ON CONFLICT (competitor_id) DO UPDATE SET
                name = excluded.name,
                domain = excluded.domain,
                industry = excluded.industry,
                tier = excluded.tier,
                tracked_urls = excluded.tracked_urls,
                updated_at = now()
            """,
            [competitor_id, name, domain, industry, tier, tracked_urls_json],
        )

    def upsert_signal(
        self,
        *,
        signal_id: str,
        competitor_id: str,
        url: str,
        signal_type: str,
        title: str,
        summary: str,
        entities_json: str,
        significance: int,
        confidence: float,
        embedding: list[float],
        source_hash: str,
        model: str,
        extracted_at: Any,
    ) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO raw.signals
                (id, competitor_id, url, signal_type, title, summary, entities,
                 significance, confidence, embedding, source_hash, model, extracted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                signal_id,
                competitor_id,
                url,
                signal_type,
                title,
                summary,
                entities_json,
                significance,
                confidence,
                embedding,
                source_hash,
                model,
                extracted_at,
            ],
        )

    def insert_change(
        self,
        *,
        change_id: str,
        competitor_id: str,
        url: str,
        signal_type: str | None,
        change_type: str,
        summary: str | None,
        significance_score: int | None,
        prev_hash: str | None,
        new_hash: str | None,
        detected_at: Any,
    ) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO raw.changes
                (change_id, competitor_id, url, signal_type, change_type, summary,
                 significance_score, prev_hash, new_hash, detected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                change_id,
                competitor_id,
                url,
                signal_type,
                change_type,
                summary,
                significance_score,
                prev_hash,
                new_hash,
                detected_at,
            ],
        )

    def log_llm_call(
        self,
        *,
        call_id: str,
        ts: Any,
        provider: str,
        model: str,
        url: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        latency_ms: int,
        ok: bool,
        error: str | None,
    ) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO raw.llm_calls
                (id, ts, provider, model, url, prompt_tokens, completion_tokens,
                 total_tokens, latency_ms, ok, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                call_id,
                ts,
                provider,
                model,
                url,
                prompt_tokens,
                completion_tokens,
                total_tokens,
                latency_ms,
                ok,
                error,
            ],
        )

    def upsert_report(
        self,
        *,
        report_id: str,
        title: str,
        week_start: Any,
        summary: str,
        body_md: str,
        created_at: Any,
    ) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO raw.reports
                (id, title, week_start, summary, body_md, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [report_id, title, week_start, summary, body_md, created_at],
        )

    # ---------------------------- reads ----------------------------------- #
    def latest_two_snapshots_per_url(self) -> list[dict[str, Any]]:
        """The two most recent distinct snapshots per URL (for diffing)."""
        rows = self.conn.execute(
            """
            WITH ranked AS (
                SELECT competitor_id, url, content_hash, clean_text, fetched_at,
                       row_number() OVER (PARTITION BY url ORDER BY fetched_at DESC) AS rn
                FROM raw.raw_pages
            )
            SELECT competitor_id, url, content_hash, clean_text, fetched_at, rn
            FROM ranked WHERE rn <= 2
            ORDER BY url, rn
            """
        ).fetchall()
        cols = ["competitor_id", "url", "content_hash", "clean_text", "fetched_at", "rn"]
        return [dict(zip(cols, r, strict=True)) for r in rows]

    def extracted_source_hashes(self) -> set[tuple[str, str]]:
        """(url, source_hash) pairs already extracted, to avoid re-extraction."""
        rows = self.conn.execute("SELECT url, source_hash FROM raw.signals").fetchall()
        return {(r[0], r[1]) for r in rows}

    def latest_page_for_url(self, url: str) -> dict[str, Any] | None:
        """Most recent snapshot for a URL (used for change detection)."""
        row = self.conn.execute(
            """
            SELECT id, competitor_id, url, content_hash, fetched_at
            FROM raw.raw_pages
            WHERE url = ?
            ORDER BY fetched_at DESC
            LIMIT 1
            """,
            [url],
        ).fetchone()
        if row is None:
            return None
        cols = ["id", "competitor_id", "url", "content_hash", "fetched_at"]
        return dict(zip(cols, row, strict=True))

    def count_raw_pages(self) -> int:
        return int(self.conn.execute("SELECT count(*) FROM raw.raw_pages").fetchone()[0])

    def count(self, table: str) -> int:
        """Row count for a raw.* table; 0 if it doesn't exist yet."""
        if not table.replace("_", "").isalnum():
            raise ValueError(f"invalid table name: {table}")
        try:
            return int(self.conn.execute(f"SELECT count(*) FROM raw.{table}").fetchone()[0])
        except duckdb.Error:
            return 0

    def query(self, sql: str, params: list[Any] | None = None) -> list[tuple]:
        return self.conn.execute(sql, params or []).fetchall()

    def close(self) -> None:
        with contextlib.suppress(Exception):
            self.conn.close()

    def __enter__(self) -> Warehouse:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


@contextlib.contextmanager
def open_warehouse(read_only: bool = False) -> Iterator[Warehouse]:
    """Context-managed warehouse from settings."""
    wh = Warehouse.from_settings(read_only=read_only)
    try:
        yield wh
    finally:
        wh.close()
