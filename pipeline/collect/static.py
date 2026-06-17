"""Static-page collector: httpx fetch + trafilatura main-text extraction.

For server-rendered pages. JS-heavy pages use the dynamic (Playwright)
collector instead - see Phase 1.
"""

from __future__ import annotations

import httpx
import trafilatura
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from pipeline.collect.base import (
    Collector,
    FetchResult,
    content_hash,
    make_page_id,
)
from pipeline.logging_setup import get_logger
from pipeline.schemas import RawPage, SourceType, utcnow

log = get_logger(__name__)

_RETRYABLE = (httpx.TransportError, httpx.HTTPStatusError)


class StaticCollector(Collector):
    """Fetch and clean server-rendered HTML pages."""

    @retry(
        retry=retry_if_exception_type(_RETRYABLE),
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

    def fetch(self, url: str) -> FetchResult:
        """Fetch a single URL, honoring robots + throttle. Never raises."""
        if not self._allowed(url):
            return FetchResult(url=url, status_code=0, text="", ok=False, error="robots-disallowed")
        self.throttle(url)
        try:
            resp = self._get(url)
        except Exception as exc:
            log.warning("fetch failed for %s: %s", url, exc)
            status = getattr(getattr(exc, "response", None), "status_code", 0) or 0
            return FetchResult(url=url, status_code=status, text="", ok=False, error=str(exc))
        return FetchResult(
            url=url,
            status_code=resp.status_code,
            text=resp.text,
            ok=True,
            headers=dict(resp.headers),
        )

    def collect(self, competitor_id: str, url: str) -> list[RawPage]:
        """Fetch a URL and build a RawPage (with cleaned main text)."""
        result = self.fetch(url)
        if not result.ok:
            return []
        clean = trafilatura.extract(result.text, include_comments=False) or ""
        # Hash the cleaned text when available (more stable than raw HTML),
        # else fall back to raw HTML.
        hash_basis = clean if clean.strip() else result.text
        chash = content_hash(hash_basis)
        return [
            RawPage(
                id=make_page_id(url, chash),
                competitor_id=competitor_id,
                url=url,
                source_type=SourceType.STATIC,
                raw_html=result.text,
                clean_text=clean or None,
                http_status=result.status_code,
                content_hash=chash,
                fetched_at=utcnow(),
            )
        ]
