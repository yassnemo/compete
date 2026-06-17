"""Extraction runner: detect changes → LLM-extract signals → persist.

Ties the cheap diff (``detect``) to the LLM client and storage. Each extracted
signal is stored with its embedding (for later semantic dedup), a ``changes``
row is recorded, and every LLM call is logged for cost tracking.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field

from pipeline.config import Settings, get_settings, load_competitors
from pipeline.detect.change import ChangeCandidate, detect_changes
from pipeline.extract.embeddings import get_embedder
from pipeline.extract.llm import ExtractionError, get_llm_client, now_ms
from pipeline.logging_setup import get_logger
from pipeline.report.alerts import AlertItem, notify
from pipeline.schemas import CompetitorsFile, SignalType, utcnow
from pipeline.storage.duckdb_store import Warehouse

log = get_logger(__name__)


@dataclass
class ExtractStats:
    candidates: int = 0
    considered: int = 0
    extracted: int = 0
    failed: int = 0
    total_tokens: int = 0
    provider: str = ""
    model: str = ""
    by_type: dict[str, int] = field(default_factory=dict)


def _signal_id(url: str, source_hash: str) -> str:
    return hashlib.sha256(f"{url}\n{source_hash}".encode()).hexdigest()[:24]


def build_hints(cfg: CompetitorsFile) -> dict[str, SignalType | None]:
    hints: dict[str, SignalType | None] = {}
    for comp in cfg.competitors:
        for tracked in comp.tracked_urls:
            hints[str(tracked.url)] = tracked.signal_hint
            hints[str(tracked.url).rstrip("/")] = tracked.signal_hint
    return hints


def _competitor_names(wh: Warehouse) -> dict[str, str]:
    rows = wh.query("SELECT competitor_id, name FROM raw.competitors")
    return {r[0]: r[1] for r in rows}


def run_detection(settings: Settings | None = None) -> list[ChangeCandidate]:
    """Compute change candidates without calling the LLM (dry run)."""
    s = settings or get_settings()
    wh = Warehouse.from_settings(s)
    try:
        embedder = get_embedder(s)
        hints = build_hints(load_competitors())
        return detect_changes(wh, embedder, s.diff_similarity_threshold, hints)
    finally:
        wh.close()


def run_extraction(
    limit: int = 0,
    provider_override: str | None = None,
    settings: Settings | None = None,
) -> ExtractStats:
    s = settings or get_settings()
    s.ensure_dirs()
    wh = Warehouse.from_settings(s)
    stats = ExtractStats()
    try:
        embedder = get_embedder(s)
        llm = get_llm_client(s, provider_override)
        stats.provider, stats.model = llm.provider, llm.model

        names = _competitor_names(wh)
        hints = build_hints(load_competitors())
        candidates = detect_changes(wh, embedder, s.diff_similarity_threshold, hints)
        stats.candidates = len(candidates)
        todo = candidates[:limit] if limit else candidates
        stats.considered = len(todo)
        alert_items: list[AlertItem] = []

        for cand in todo:
            name = names.get(cand.competitor_id, cand.competitor_id)
            t0 = now_ms()
            try:
                result = llm.extract_signal(cand.text, cand.signal_hint, name)
            except ExtractionError as exc:
                wh.log_llm_call(
                    call_id=uuid.uuid4().hex,
                    ts=utcnow(),
                    provider=llm.provider,
                    model=llm.model,
                    url=cand.url,
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    latency_ms=now_ms() - t0,
                    ok=False,
                    error=str(exc),
                )
                stats.failed += 1
                continue

            latency = now_ms() - t0
            sig = result.signal
            embedding = embedder.embed_one(cand.text)
            sid = _signal_id(cand.url, cand.new_hash)

            wh.upsert_signal(
                signal_id=sid,
                competitor_id=cand.competitor_id,
                url=cand.url,
                signal_type=str(sig.signal_type),
                title=sig.title,
                summary=sig.summary,
                entities_json=json.dumps(sig.entities),
                significance=sig.significance,
                confidence=sig.confidence,
                embedding=embedding,
                source_hash=cand.new_hash,
                model=llm.model,
                extracted_at=utcnow(),
            )
            wh.insert_change(
                change_id=f"chg-{sid}",
                competitor_id=cand.competitor_id,
                url=cand.url,
                signal_type=str(sig.signal_type),
                change_type=str(cand.change_type),
                summary=sig.summary,
                significance_score=sig.significance,
                prev_hash=cand.prev_hash,
                new_hash=cand.new_hash,
                detected_at=utcnow(),
            )
            wh.log_llm_call(
                call_id=uuid.uuid4().hex,
                ts=utcnow(),
                provider=llm.provider,
                model=llm.model,
                url=cand.url,
                prompt_tokens=result.usage.prompt_tokens,
                completion_tokens=result.usage.completion_tokens,
                total_tokens=result.usage.total_tokens,
                latency_ms=latency,
                ok=True,
                error=None,
            )
            stats.extracted += 1
            stats.total_tokens += result.usage.total_tokens
            key = str(sig.signal_type)
            stats.by_type[key] = stats.by_type.get(key, 0) + 1

            if sig.significance >= s.alert_min_significance:
                alert_items.append(
                    AlertItem(
                        competitor=name,
                        signal_type=str(sig.signal_type),
                        title=sig.title,
                        significance=sig.significance,
                        url=cand.url,
                    )
                )

        if s.alerts_enabled and alert_items:
            notify(alert_items, s)

        return stats
    finally:
        wh.close()
