"""RSS / Atom feed collector.

A feed expands to many entries; each entry becomes its own RawPage keyed by its
link, so downstream change-detection treats new posts as new signals. The feed
URL itself is fetched politely (robots + throttle), then parsed offline with
feedparser.
"""

from __future__ import annotations

from datetime import datetime
from time import mktime

import feedparser
import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from pipeline.collect.base import Collector, content_hash, make_page_id
from pipeline.logging_setup import get_logger
from pipeline.schemas import RawPage, SourceType, utcnow

log = get_logger(__name__)


def _entry_text(entry: feedparser.FeedParserDict) -> str:
    """Best-effort body text from a feed entry."""
    if entry.get("content"):
        return " ".join(c.get("value", "") for c in entry["content"])
    return entry.get("summary") or entry.get("description") or ""


def _entry_published(entry: feedparser.FeedParserDict) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        parsed = entry.get(key)
        if parsed:
            try:
                return datetime.fromtimestamp(mktime(parsed))
            except (ValueError, OverflowError):
                continue
    return None


class RSSCollector(Collector):
    """Fetch and parse an RSS/Atom feed into per-entry RawPages."""

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
        wait=wait_exponential(multiplier=1, min=2, max=20),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def _get(self, url: str) -> httpx.Response:
        resp = httpx.get(
            url,
            headers={"User-Agent": self.settings.user_agent},
            timeout=self.settings.request_timeout,
            follow_redirects=True,
        )
        resp.raise_for_status()
        return resp

    def collect(self, competitor_id: str, url: str, limit: int = 50) -> list[RawPage]:
        if not self._allowed(url):
            return []
        self.throttle(url)
        try:
            resp = self._get(url)
        except Exception as exc:
            log.warning("RSS fetch failed for %s: %s", url, exc)
            return []

        feed = feedparser.parse(resp.content)
        if feed.bozo and not feed.entries:
            log.warning(
                "RSS parse produced no entries for %s (%s)", url, feed.get("bozo_exception")
            )
            return []

        pages: list[RawPage] = []
        for entry in feed.entries[:limit]:
            link = entry.get("link") or url
            title = entry.get("title", "(untitled)")
            body = _entry_text(entry)
            published = _entry_published(entry)
            # Hash on title+body so edits to a post register as a change.
            text = f"{title}\n{body}".strip()
            chash = content_hash(text or link)
            pages.append(
                RawPage(
                    id=make_page_id(link, chash),
                    competitor_id=competitor_id,
                    url=link,
                    source_type=SourceType.RSS,
                    raw_html=body,
                    clean_text=f"{title}\n\n{body}".strip() or None,
                    http_status=resp.status_code,
                    content_hash=chash,
                    fetched_at=published.astimezone() if published else utcnow(),
                )
            )
        log.info("RSS %s -> %d entries", url, len(pages))
        return pages
