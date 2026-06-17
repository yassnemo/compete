"""Tests for collection primitives (hashing, ids, throttle)."""

from __future__ import annotations

import time

from pipeline.collect.base import Throttler, content_hash, make_page_id


def test_content_hash_normalizes_whitespace() -> None:
    a = content_hash("hello\n  world  \n")
    b = content_hash("hello\nworld")
    assert a == b


def test_content_hash_differs_on_change() -> None:
    assert content_hash("v1 pricing $10") != content_hash("v2 pricing $20")


def test_make_page_id_deterministic() -> None:
    h = content_hash("abc")
    assert make_page_id("https://x.com", h) == make_page_id("https://x.com", h)
    assert make_page_id("https://x.com", h) != make_page_id("https://y.com", h)


def test_throttler_enforces_interval() -> None:
    t = Throttler(min_interval=0.2)
    url = "https://example.com/a"
    start = time.monotonic()
    t.wait(url)  # first call: no wait
    t.wait(url)  # second call: should wait ~0.2s
    elapsed = time.monotonic() - start
    assert elapsed >= 0.18
