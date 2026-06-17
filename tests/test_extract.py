"""Phase 2 tests - embeddings, LLM mock + retry loop, detection, runner."""

from __future__ import annotations

from pathlib import Path

import pytest
from pipeline.config import Settings
from pipeline.detect.change import detect_changes
from pipeline.extract.embeddings import HashingEmbedder, cosine
from pipeline.extract.llm import (
    LLMClient,
    MockClient,
    TokenUsage,
)
from pipeline.schemas import RawPage, Signal, SignalType, SourceType, utcnow
from pipeline.storage.duckdb_store import Warehouse
from pydantic import ValidationError


# ------------------------------ embeddings -------------------------------- #
def test_hashing_embedder_deterministic_and_normalized() -> None:
    emb = HashingEmbedder(dim=128)
    a = emb.embed_one("Anthropic launches Claude Opus 4.8 with new pricing")
    b = emb.embed_one("Anthropic launches Claude Opus 4.8 with new pricing")
    assert a == b
    assert pytest.approx(cosine(a, a), abs=1e-6) == 1.0


def test_cosine_minor_edit_vs_real_change() -> None:
    emb = HashingEmbedder(dim=256)
    base = "Our Pro plan costs twenty dollars per month and includes priority support."
    minor = base + " "  # trivial edit
    different = "We are hiring a senior platform engineer to join our infrastructure team."
    assert cosine(emb.embed_one(base), emb.embed_one(minor)) > 0.95
    assert cosine(emb.embed_one(base), emb.embed_one(different)) < 0.5


# ------------------------------ mock LLM ---------------------------------- #
def test_mock_client_extracts_valid_signal() -> None:
    client = MockClient()
    res = client.extract_signal(
        "Introducing our new flagship model, now available to all customers.",
        signal_hint=None,
        competitor="Acme",
    )
    assert isinstance(res.signal, Signal)
    assert res.signal.signal_type == SignalType.PRODUCT_LAUNCH
    assert res.attempts == 1
    assert res.usage.total_tokens > 0


def test_mock_client_respects_hint() -> None:
    client = MockClient()
    res = client.extract_signal("Generic text.", SignalType.FUNDING_NEWS, "Acme")
    assert res.signal.signal_type == SignalType.FUNDING_NEWS


class _FlakyClient(LLMClient):
    """Fails schema validation once, then succeeds - exercises the retry loop."""

    provider = "flaky"

    def __init__(self) -> None:
        super().__init__()
        self.model = "flaky-1"
        self.calls = 0

    def _complete(self, messages, signal_hint):
        self.calls += 1
        if self.calls == 1:
            # title="" violates min_length=1 -> ValidationError
            Signal(
                signal_type=SignalType.OTHER, title="", summary="x", significance=3, confidence=0.5
            )
        return (
            Signal(
                signal_type=SignalType.OTHER,
                title="recovered",
                summary="ok",
                significance=2,
                confidence=0.5,
            ),
            TokenUsage(1, 1, 2),
        )


def test_retry_loop_recovers_after_validation_error() -> None:
    client = _FlakyClient()
    res = client.extract_signal("text", None, "Acme")
    assert client.calls == 2
    assert res.attempts == 2
    assert res.signal.title == "recovered"


def test_signal_validation_actually_raises() -> None:
    with pytest.raises(ValidationError):
        Signal(signal_type=SignalType.OTHER, title="", summary="x", significance=3, confidence=0.5)


# ------------------------------ detection --------------------------------- #
def _page(url: str, text: str, chash: str, fetched) -> RawPage:
    return RawPage(
        id=f"{chash}",
        competitor_id="acme",
        url=url,
        source_type=SourceType.STATIC,
        raw_html="<html></html>",
        clean_text=text,
        content_hash=chash,
        http_status=200,
        fetched_at=fetched,
    )


def test_detect_new_and_skip_already_extracted(tmp_path: Path) -> None:
    wh = Warehouse(tmp_path / "t.duckdb")
    emb = HashingEmbedder(dim=128)
    wh.upsert_raw_page(_page("https://acme.com/a", "hello world", "h1", utcnow()))

    cands = detect_changes(wh, emb, threshold=0.9)
    assert len(cands) == 1
    assert str(cands[0].change_type) == "new"

    # Once a signal exists for (url, hash), it's no longer a candidate.
    wh.upsert_signal(
        signal_id="s1",
        competitor_id="acme",
        url="https://acme.com/a",
        signal_type="other",
        title="t",
        summary="s",
        entities_json="[]",
        significance=2,
        confidence=0.5,
        embedding=emb.embed_one("hello world"),
        source_hash="h1",
        model="mock-1",
        extracted_at=utcnow(),
    )
    assert detect_changes(wh, emb, threshold=0.9) == []
    wh.close()


def test_detect_minor_edit_skipped(tmp_path: Path) -> None:
    from datetime import timedelta

    wh = Warehouse(tmp_path / "t.duckdb")
    emb = HashingEmbedder(dim=256)
    t0 = utcnow()
    base = "Our Pro plan costs twenty dollars per month with priority support included."
    wh.upsert_raw_page(_page("https://acme.com/p", base, "hp1", t0))
    wh.upsert_raw_page(_page("https://acme.com/p", base + " ", "hp2", t0 + timedelta(hours=1)))
    # New hash but ~identical text -> minor edit -> skipped.
    assert detect_changes(wh, emb, threshold=0.9) == []
    wh.close()


# ------------------------------ runner ------------------------------------ #
def test_run_extraction_end_to_end(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from pipeline.extract.runner import run_extraction

    db = tmp_path / "t.duckdb"
    monkeypatch.setenv("COMPETE_DUCKDB_PATH", str(db))
    monkeypatch.setenv("COMPETE_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("COMPETE_LLM_PROVIDER", "mock")
    monkeypatch.setenv("COMPETE_EMBED_PROVIDER", "hashing")
    settings = Settings()

    wh = Warehouse(db)
    wh.upsert_competitor("acme", "Acme", "acme.com", "SaaS", 1, "[]")
    wh.upsert_raw_page(
        _page(
            "https://acme.com/news",
            "Introducing our new flagship model, now available to all customers.",
            "hn1",
            utcnow(),
        )
    )
    wh.close()

    stats = run_extraction(settings=settings)
    assert stats.extracted == 1
    assert stats.failed == 0
    assert stats.provider == "mock"
    assert stats.total_tokens > 0

    wh = Warehouse.from_settings(settings, read_only=True)
    assert wh.count("signals") == 1
    assert wh.count("changes") == 1
    assert wh.count("llm_calls") == 1
    wh.close()
