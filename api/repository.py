"""SQL queries over the marts, returning plain dicts for the API layer.

Marts live in ``main_marts``; operational competitor CRUD targets ``raw.competitors``.
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from api.db import ApiDB

# Content-type signals used for the posting-cadence chart.
_CADENCE_TYPES = ("blog_post", "press_release", "product_launch")


def _entities(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(x) for x in raw]
    try:
        parsed = json.loads(raw)
        return [str(x) for x in parsed] if isinstance(parsed, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def _tracked_urls(raw: Any) -> list[dict[str, Any]]:
    if raw is None:
        return []
    data = raw if isinstance(raw, list) else json.loads(raw)
    out = []
    for t in data:
        out.append(
            {
                "url": t.get("url"),
                "source_type": t.get("source_type", "static"),
                "signal_hint": t.get("signal_hint"),
            }
        )
    return out


# ------------------------------ competitors ------------------------------- #
def list_competitors(db: ApiDB) -> list[dict[str, Any]]:
    rows = db.query(
        """
        SELECT c.competitor_id, c.name, c.domain, c.industry, c.tier, c.tracked_urls,
               coalesce(cast(json_array_length(c.tracked_urls) as integer), 0) AS tracked_url_count,
               coalesce(s.signal_count, 0) AS signal_count,
               coalesce(s.high_significance_count, 0) AS high_significance_count,
               s.last_signal_at
        FROM raw.competitors c
        LEFT JOIN (
            SELECT competitor_id, count(*) AS signal_count,
                   count(*) FILTER (WHERE significance >= 4) AS high_significance_count,
                   max(extracted_at) AS last_signal_at
            FROM raw.signals GROUP BY 1
        ) s USING (competitor_id)
        ORDER BY signal_count DESC, c.name
        """
    )
    return [_competitor_row(r) for r in rows]


def get_competitor(db: ApiDB, competitor_id: str) -> dict[str, Any] | None:
    rows = db.query(
        """
        SELECT c.competitor_id, c.name, c.domain, c.industry, c.tier, c.tracked_urls,
               coalesce(cast(json_array_length(c.tracked_urls) as integer), 0) AS tracked_url_count,
               coalesce(s.signal_count, 0) AS signal_count,
               coalesce(s.high_significance_count, 0) AS high_significance_count,
               s.last_signal_at
        FROM raw.competitors c
        LEFT JOIN (
            SELECT competitor_id, count(*) AS signal_count,
                   count(*) FILTER (WHERE significance >= 4) AS high_significance_count,
                   max(extracted_at) AS last_signal_at
            FROM raw.signals GROUP BY 1
        ) s USING (competitor_id)
        WHERE c.competitor_id = ?
        """,
        [competitor_id],
    )
    return _competitor_row(rows[0]) if rows else None


def _competitor_row(r: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": r["competitor_id"],
        "name": r["name"],
        "domain": r["domain"],
        "industry": r["industry"],
        "tier": r["tier"],
        "tracked_urls": _tracked_urls(r.get("tracked_urls")),
        "tracked_url_count": r["tracked_url_count"],
        "signal_count": r["signal_count"],
        "high_significance_count": r["high_significance_count"],
        "last_signal_at": r["last_signal_at"],
    }


def upsert_competitor(
    db: ApiDB,
    *,
    competitor_id: str,
    name: str,
    domain: str | None,
    industry: str | None,
    tier: int,
    tracked_urls: list[dict[str, Any]],
) -> None:
    db.execute(
        """
        INSERT INTO raw.competitors
            (competitor_id, name, domain, industry, tier, tracked_urls, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, now())
        ON CONFLICT (competitor_id) DO UPDATE SET
            name = excluded.name, domain = excluded.domain, industry = excluded.industry,
            tier = excluded.tier, tracked_urls = excluded.tracked_urls, updated_at = now()
        """,
        [competitor_id, name, domain, industry, tier, json.dumps(tracked_urls)],
    )


def delete_competitor(db: ApiDB, competitor_id: str) -> None:
    db.execute("DELETE FROM raw.competitors WHERE competitor_id = ?", [competitor_id])


# --------------------------- signals & changes ---------------------------- #
def _signal_filters(
    competitor: str | None,
    signal_type: str | None,
    min_significance: int | None,
    date_from: date | None,
    date_to: date | None,
    sig_col: str,
    date_col: str,
) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if competitor:
        clauses.append("competitor_id = ?")
        params.append(competitor)
    if signal_type:
        clauses.append("signal_type = ?")
        params.append(signal_type)
    if min_significance is not None:
        clauses.append(f"{sig_col} >= ?")
        params.append(min_significance)
    if date_from:
        clauses.append(f"{date_col} >= ?")
        params.append(date_from)
    if date_to:
        clauses.append(f"{date_col} <= ?")
        params.append(date_to)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return where, params


def list_signals(
    db: ApiDB,
    *,
    competitor=None,
    signal_type=None,
    min_significance=None,
    date_from=None,
    date_to=None,
    limit=50,
    offset=0,
) -> tuple[list[dict], int]:
    where, params = _signal_filters(
        competitor,
        signal_type,
        min_significance,
        date_from,
        date_to,
        "significance",
        "extracted_at",
    )
    total = db.scalar(f"SELECT count(*) FROM raw.signals{where}", params, default=0)
    rows = db.query(
        f"""
        SELECT id AS signal_id, competitor_id, url, signal_type, title, summary,
               entities, significance, confidence, extracted_at
        FROM raw.signals{where}
        ORDER BY extracted_at DESC NULLS LAST
        LIMIT ? OFFSET ?
        """,
        [*params, limit, offset],
    )
    for r in rows:
        r["entities"] = _entities(r.get("entities"))
    return rows, int(total)


def list_changes(
    db: ApiDB,
    *,
    competitor=None,
    signal_type=None,
    min_significance=None,
    date_from=None,
    date_to=None,
    limit=50,
    offset=0,
) -> tuple[list[dict], int]:
    where, params = _signal_filters(
        competitor,
        signal_type,
        min_significance,
        date_from,
        date_to,
        "weighted_significance",
        "detected_at",
    )
    total = db.scalar(f"SELECT count(*) FROM main_marts.fct_changes{where}", params, default=0)
    rows = db.query(
        f"""
        SELECT change_id, competitor_id, url, change_type, signal_type, title, summary,
               significance_score, weighted_significance, confidence, detected_at
        FROM main_marts.fct_changes{where}
        ORDER BY detected_at DESC NULLS LAST, weighted_significance DESC
        LIMIT ? OFFSET ?
        """,
        [*params, limit, offset],
    )
    return rows, int(total)


# ------------------------------- analytics -------------------------------- #
def pricing_history(db: ApiDB, competitor_id: str) -> list[dict[str, Any]]:
    return db.query(
        """
        SELECT competitor_id, plan, price, currency, captured_at
        FROM main_marts.fct_pricing_history
        WHERE competitor_id = ? ORDER BY captured_at, plan
        """,
        [competitor_id],
    )


def hiring(db: ApiDB, competitor_id: str) -> list[dict[str, Any]]:
    return db.query(
        """
        SELECT competitor_id, role, location, posted_at, removed_at
        FROM main_marts.fct_hiring
        WHERE competitor_id = ? ORDER BY posted_at DESC NULLS LAST, role
        """,
        [competitor_id],
    )


def cadence(db: ApiDB, competitor_id: str) -> list[dict[str, Any]]:
    placeholders = ", ".join("?" for _ in _CADENCE_TYPES)
    return db.query(
        f"""
        SELECT cast(date_trunc('week', extracted_at) AS date) AS week, count(*) AS count
        FROM raw.signals
        WHERE competitor_id = ? AND signal_type IN ({placeholders})
        GROUP BY 1 ORDER BY 1
        """,
        [competitor_id, *_CADENCE_TYPES],
    )


def overview(db: ApiDB) -> dict[str, Any]:
    competitors = db.scalar("SELECT count(*) FROM raw.competitors", default=0)
    signals_total = db.scalar("SELECT count(*) FROM raw.signals", default=0)
    signals_week = db.scalar(
        "SELECT count(*) FROM raw.signals WHERE extracted_at >= now() - INTERVAL 7 DAY", default=0
    )
    high_sig = db.scalar(
        "SELECT count(*) FROM main_marts.fct_changes WHERE weighted_significance >= 4", default=0
    )
    alerts = db.scalar(
        "SELECT count(*) FROM main_marts.fct_changes "
        "WHERE weighted_significance >= 4 AND detected_at >= now() - INTERVAL 7 DAY",
        default=0,
    )
    changes_week = db.scalar(
        "SELECT count(*) FROM main_marts.fct_changes WHERE detected_at >= now() - INTERVAL 7 DAY",
        default=0,
    )
    by_type = db.query(
        "SELECT signal_type, count(*) AS count FROM raw.signals GROUP BY 1 ORDER BY count DESC"
    )
    trend = db.query(
        """
        SELECT week, sum(total_changes) AS total_changes,
               sum(high_significance_changes) AS high_significance_changes
        FROM main_marts.agg_weekly_competitor
        GROUP BY week ORDER BY week DESC LIMIT 8
        """
    )
    trend.reverse()
    return {
        "competitors_tracked": int(competitors),
        "signals_total": int(signals_total),
        "signals_this_week": int(signals_week),
        "high_significance_count": int(high_sig),
        "active_alerts": int(alerts),
        "changes_this_week": int(changes_week),
        "by_type": by_type,
        "weekly_trend": trend,
    }


# -------------------------------- reports --------------------------------- #
def list_reports(db: ApiDB) -> list[dict[str, Any]]:
    return db.query(
        "SELECT id, title, week_start, summary, created_at FROM raw.reports "
        "ORDER BY created_at DESC"
    )


def get_report(db: ApiDB, report_id: str) -> dict[str, Any] | None:
    return db.query_one(
        "SELECT id, title, week_start, summary, body_md, created_at FROM raw.reports WHERE id = ?",
        [report_id],
    )
