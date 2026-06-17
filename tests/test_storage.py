"""Tests for the DuckDB storage layer (in a temp file)."""

from __future__ import annotations

from pathlib import Path

from pipeline.schemas import RawPage, SourceType
from pipeline.storage.duckdb_store import Warehouse


def _make_page(url: str, chash: str) -> RawPage:
    return RawPage(
        id=f"id-{chash[:8]}",
        competitor_id="acme",
        url=url,
        source_type=SourceType.STATIC,
        raw_html="<html></html>",
        clean_text="hello world",
        content_hash=chash,
        http_status=200,
    )


def test_bootstrap_and_insert(tmp_path: Path) -> None:
    db = tmp_path / "t.duckdb"
    wh = Warehouse(db)
    assert wh.count_raw_pages() == 0
    wh.upsert_raw_page(_make_page("https://acme.com", "h1"))
    assert wh.count_raw_pages() == 1
    wh.close()


def test_latest_page_for_url(tmp_path: Path) -> None:
    wh = Warehouse(tmp_path / "t.duckdb")
    wh.upsert_raw_page(_make_page("https://acme.com/p", "hash_old"))
    latest = wh.latest_page_for_url("https://acme.com/p")
    assert latest is not None
    assert latest["content_hash"] == "hash_old"
    assert latest["competitor_id"] == "acme"
    wh.close()


def test_upsert_competitor(tmp_path: Path) -> None:
    wh = Warehouse(tmp_path / "t.duckdb")
    wh.upsert_competitor("acme", "Acme", "acme.com", "SaaS", 1, "[]")
    wh.upsert_competitor("acme", "Acme Inc", "acme.com", "SaaS", 1, "[]")  # update
    rows = wh.query("SELECT name FROM raw.competitors WHERE competitor_id = 'acme'")
    assert rows[0][0] == "Acme Inc"
    wh.close()
