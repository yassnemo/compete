"""Tests for extraction/config schema validation."""

from __future__ import annotations

import pytest
from pipeline.schemas import (
    CompetitorsFile,
    Signal,
    SignalType,
    SourceType,
)
from pydantic import ValidationError


def test_signal_valid() -> None:
    s = Signal(
        signal_type=SignalType.PRICING_CHANGE,
        title="New Pro tier",
        summary="Launched a Pro plan at $20/mo. Includes priority support.",
        entities=["Pro", "Pro", "  ", "Support"],
        significance=4,
        confidence=0.9,
    )
    assert s.signal_type is SignalType.PRICING_CHANGE
    # dedupe + strip applied
    assert s.entities == ["Pro", "Support"]


@pytest.mark.parametrize("bad", [0, 6, -1])
def test_signal_significance_bounds(bad: int) -> None:
    with pytest.raises(ValidationError):
        Signal(
            signal_type=SignalType.OTHER,
            title="x",
            summary="y",
            significance=bad,
            confidence=0.5,
        )


def test_signal_confidence_bounds() -> None:
    with pytest.raises(ValidationError):
        Signal(
            signal_type=SignalType.OTHER,
            title="x",
            summary="y",
            significance=3,
            confidence=1.5,
        )


def test_competitors_file_parsing() -> None:
    data = {
        "defaults": {"throttle_seconds": 1.5, "respect_robots": True},
        "competitors": [
            {
                "id": "acme",
                "name": "Acme",
                "domain": "acme.com",
                "tier": 1,
                "tracked_urls": [
                    {"url": "https://acme.com/news", "source_type": "static"},
                    {"url": "https://acme.com/feed", "source_type": "rss"},
                ],
            }
        ],
    }
    cfg = CompetitorsFile.model_validate(data)
    assert cfg.competitors[0].id == "acme"
    assert cfg.competitors[0].tracked_urls[1].source_type is SourceType.RSS


def test_competitor_id_pattern_rejected() -> None:
    with pytest.raises(ValidationError):
        CompetitorsFile.model_validate(
            {"competitors": [{"id": "Bad ID!", "name": "x", "domain": "x.com"}]}
        )
