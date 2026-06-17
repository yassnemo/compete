"""Phase 6 tests - report generation, PDF rendering, alert gating."""

from __future__ import annotations

from pathlib import Path

import pytest
from pipeline.config import Settings
from pipeline.report.alerts import AlertItem, build_message, notify
from pipeline.report.pdf import render_report_pdf
from pipeline.storage.duckdb_store import Warehouse


# ------------------------------- PDF -------------------------------------- #
def test_render_pdf_returns_valid_bytes() -> None:
    md = "# Title\n\n## Section\nBody text with **bold**.\n\n- bullet one\n- bullet two\n"
    pdf = render_report_pdf("Weekly Brief", md)
    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 500


def test_render_pdf_handles_unicode() -> None:
    md = "# Brief - week of 2026\n\nSignificance ≥ 4 with “smart quotes”.\n"
    pdf = render_report_pdf("t", md)
    assert pdf.startswith(b"%PDF")


# ------------------------------ alerts ------------------------------------ #
def test_build_message_lists_items() -> None:
    items = [
        AlertItem("Anthropic", "product_launch", "Opus 4.8", 5, "https://x"),
        AlertItem("OpenAI", "pricing_change", "Price cut", 4, None),
    ]
    msg = build_message(items)
    assert "Anthropic" in msg and "Opus 4.8" in msg
    assert "OpenAI" in msg


def test_notify_disabled_is_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COMPETE_ALERTS_ENABLED", "false")
    s = Settings()
    result = notify([AlertItem("A", "other", "t", 5)], s)
    assert result["enabled"] is False
    assert result["sent"] == []


def test_notify_enabled_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COMPETE_ALERTS_ENABLED", "true")
    monkeypatch.setenv("COMPETE_ALERT_MIN_SIGNIFICANCE", "4")
    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
    s = Settings()
    # significance 3 is below threshold -> filtered out; 5 stays -> dry-run.
    result = notify(
        [AlertItem("A", "other", "low", 3), AlertItem("B", "funding_news", "big", 5)], s
    )
    assert result["eligible"] == 1
    assert "dry-run" in result["sent"]


# --------------------------- report generation ---------------------------- #
def test_build_weekly_report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from pipeline.report.generate import build_weekly_report

    db = tmp_path / "r.duckdb"
    monkeypatch.setenv("COMPETE_DUCKDB_PATH", str(db))
    monkeypatch.setenv("COMPETE_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("COMPETE_LLM_PROVIDER", "mock")
    s = Settings()

    # Seed a fct_changes mart directly (report reads main_marts.fct_changes).
    wh = Warehouse(db)
    wh.conn.execute("CREATE SCHEMA IF NOT EXISTS main_marts")
    wh.conn.execute(
        """
        CREATE TABLE main_marts.fct_changes AS
        SELECT * FROM (VALUES
            ('c1','acme','u1','new','product_launch','Acme 2.0','Launched',5,5,0.9,now()),
            ('c2','beta','u2','new','pricing_change','Beta price cut','Cheaper',4,4,0.9,now())
        ) AS t(change_id, competitor_id, url, change_type, signal_type, title, summary,
               significance_score, weighted_significance, confidence, detected_at)
        """
    )
    wh.conn.execute("CREATE SCHEMA IF NOT EXISTS main_marts")
    wh.conn.execute(
        """
        CREATE TABLE main_marts.dim_competitors AS
        SELECT * FROM (VALUES ('acme','Acme'), ('beta','Beta')) AS t(competitor_id, name)
        """
    )
    wh.close()

    result = build_weekly_report(s)
    assert "Executive summary" in result.body_md
    assert "Top changes" in result.body_md
    assert "Acme" in result.body_md

    # Stored and retrievable.
    wh = Warehouse.from_settings(s, read_only=True)
    assert wh.count("reports") == 1
    wh.close()
