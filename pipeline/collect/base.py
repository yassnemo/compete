"""Shared collection primitives: hashing, robots.txt, throttling, IDs.

All collectors fetch *public* pages only, honor robots.txt by default, throttle
politely, and send an honest User-Agent. These are hard requirements, not
options to disable casually.
"""

from __future__ import annotations

import hashlib
import threading
import time
import urllib.robotparser
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

import httpx

from pipeline.config import Settings, get_settings
from pipeline.logging_setup import get_logger

log = get_logger(__name__)


def content_hash(text: str) -> str:
    """Stable SHA-256 of normalized content (used for change detection)."""
    normalized = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def make_page_id(url: str, content_hash_value: str) -> str:
    """Deterministic id for a (url, content) snapshot."""
    h = hashlib.sha256(f"{url}\n{content_hash_value}".encode()).hexdigest()
    return h[:24]


@dataclass
class FetchResult:
    url: str
    status_code: int
    text: str
    ok: bool
    error: str | None = None
    headers: dict[str, str] = field(default_factory=dict)


class RobotsCache:
    """Per-host robots.txt cache with allow/deny checks."""

    def __init__(self, user_agent: str) -> None:
        self.user_agent = user_agent
        self._cache: dict[str, urllib.robotparser.RobotFileParser] = {}
        self._lock = threading.Lock()

    def _parser_for(self, url: str) -> urllib.robotparser.RobotFileParser | None:
        parsed = urlparse(url)
        host = f"{parsed.scheme}://{parsed.netloc}"
        with self._lock:
            if host in self._cache:
                return self._cache[host]
        robots_url = urljoin(host, "/robots.txt")
        rp = urllib.robotparser.RobotFileParser()
        try:
            resp = httpx.get(
                robots_url,
                headers={"User-Agent": self.user_agent},
                timeout=10.0,
                follow_redirects=True,
            )
            if resp.status_code >= 400:
                rp = _AllowAll()  # type: ignore[assignment]
            else:
                rp.parse(resp.text.splitlines())
        except Exception as exc:  # network failure -> fail open but log
            log.warning("robots.txt fetch failed for %s (%s); allowing", host, exc)
            rp = _AllowAll()  # type: ignore[assignment]
        with self._lock:
            self._cache[host] = rp
        return rp

    def can_fetch(self, url: str) -> bool:
        rp = self._parser_for(url)
        if rp is None:
            return True
        return rp.can_fetch(self.user_agent, url)

    def crawl_delay(self, url: str) -> float | None:
        """robots.txt Crawl-delay for our UA, if declared."""
        rp = self._parser_for(url)
        if rp is None:
            return None
        try:
            delay = rp.crawl_delay(self.user_agent)
        except Exception:
            return None
        return float(delay) if delay is not None else None


class _AllowAll(urllib.robotparser.RobotFileParser):
    """Fallback parser that permits everything (missing/broken robots.txt)."""

    def can_fetch(self, useragent: str, url: str) -> bool:
        return True


class Throttler:
    """Simple per-host minimum-interval throttle (thread-safe)."""

    def __init__(self, min_interval: float) -> None:
        self.min_interval = min_interval
        self._last: dict[str, float] = {}
        self._lock = threading.Lock()

    def wait(self, url: str, min_interval: float | None = None) -> None:
        interval = self.min_interval if min_interval is None else min_interval
        host = urlparse(url).netloc
        with self._lock:
            now = time.monotonic()
            last = self._last.get(host, 0.0)
            delta = now - last
            if delta < interval:
                time.sleep(interval - delta)
            self._last[host] = time.monotonic()


class Collector:
    """Base collector holding shared settings, robots cache, and throttle."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.robots = RobotsCache(self.settings.user_agent)
        self.throttler = Throttler(self.settings.throttle_seconds)

    def _allowed(self, url: str) -> bool:
        if not self.settings.respect_robots:
            return True
        allowed = self.robots.can_fetch(url)
        if not allowed:
            log.warning("robots.txt disallows fetching %s - skipping", url)
        return allowed

    def _effective_delay(self, url: str) -> float:
        """Honor the stricter of our configured throttle and robots Crawl-delay."""
        base = self.settings.throttle_seconds
        if not self.settings.respect_robots:
            return base
        declared = self.robots.crawl_delay(url)
        return max(base, declared) if declared is not None else base

    def throttle(self, url: str) -> None:
        self.throttler.wait(url, self._effective_delay(url))
