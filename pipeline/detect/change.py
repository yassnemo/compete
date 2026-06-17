"""Snapshot-diff change detection.

Two cheap, deterministic stages decide whether the (expensive) LLM runs at all
(see ADR 0002):

1. **Content hash** - a snapshot whose content_hash was already extracted is
   skipped outright.
2. **Embedding cosine** - when a URL has a new hash vs its previous snapshot,
   we compare embeddings. similarity >= threshold ⇒ a minor edit (skip);
   below ⇒ a real change to extract.

A URL seen for the first time is a NEW change. The LLM never decides *whether*
something changed - only *what* the change means, downstream.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from pipeline.extract.embeddings import Embedder, cosine
from pipeline.logging_setup import get_logger
from pipeline.schemas import ChangeType, SignalType
from pipeline.storage.duckdb_store import Warehouse

log = get_logger(__name__)


@dataclass
class ChangeCandidate:
    competitor_id: str
    url: str
    text: str
    new_hash: str
    prev_hash: str | None
    change_type: ChangeType
    signal_hint: SignalType | None
    similarity: float | None


def detect_changes(
    wh: Warehouse,
    embedder: Embedder,
    threshold: float,
    hints: dict[str, SignalType | None] | None = None,
) -> list[ChangeCandidate]:
    """Return the snapshots that represent real, not-yet-extracted changes."""
    hints = hints or {}
    snaps = wh.latest_two_snapshots_per_url()
    by_url: dict[str, list[dict]] = defaultdict(list)
    for s in snaps:
        by_url[s["url"]].append(s)

    already = wh.extracted_source_hashes()
    candidates: list[ChangeCandidate] = []

    for url, items in by_url.items():
        items.sort(key=lambda x: x["rn"])
        cur = items[0]
        prev = items[1] if len(items) > 1 else None
        new_hash = cur["content_hash"]

        if (url, new_hash) in already:
            continue  # this exact content was already turned into a signal

        hint = hints.get(url)
        if prev is None:
            candidates.append(
                ChangeCandidate(
                    competitor_id=cur["competitor_id"],
                    url=url,
                    text=cur["clean_text"] or "",
                    new_hash=new_hash,
                    prev_hash=None,
                    change_type=ChangeType.NEW,
                    signal_hint=hint,
                    similarity=None,
                )
            )
            continue

        sim = cosine(
            embedder.embed_one(cur["clean_text"] or ""),
            embedder.embed_one(prev["clean_text"] or ""),
        )
        if sim >= threshold:
            continue  # minor edit - not worth an LLM call
        candidates.append(
            ChangeCandidate(
                competitor_id=cur["competitor_id"],
                url=url,
                text=cur["clean_text"] or "",
                new_hash=new_hash,
                prev_hash=prev["content_hash"],
                change_type=ChangeType.UPDATED,
                signal_hint=hint,
                similarity=sim,
            )
        )

    log.info("detected %d change candidate(s)", len(candidates))
    return candidates
