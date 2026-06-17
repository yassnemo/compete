"""Dynamic-page collector using Playwright (for JS-rendered pages).

Requires the Playwright browser binaries:  ``playwright install chromium``
(documented in RUNBOOK). The import is lazy so the rest of the pipeline works
without browsers installed; a missing browser yields a clear, actionable error
rather than an import-time crash.
"""

from __future__ import annotations

import trafilatura

from pipeline.collect.base import Collector, content_hash, make_page_id
from pipeline.logging_setup import get_logger
from pipeline.schemas import RawPage, SourceType, utcnow

log = get_logger(__name__)


class DynamicCollector(Collector):
    """Render a page with headless Chromium, then extract clean text."""

    def __init__(self, *args: object, wait_until: str = "networkidle", **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self.wait_until = wait_until

    def collect(self, competitor_id: str, url: str) -> list[RawPage]:
        if not self._allowed(url):
            return []

        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:  # pragma: no cover - import guard
            log.error(
                "Playwright not installed (%s). `uv sync` then `playwright install chromium`.", exc
            )
            return []

        self.throttle(url)
        html = ""
        status: int | None = None
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                try:
                    context = browser.new_context(user_agent=self.settings.user_agent)
                    page = context.new_page()
                    response = page.goto(
                        url,
                        wait_until=self.wait_until,  # type: ignore[arg-type]
                        timeout=int(self.settings.request_timeout * 1000),
                    )
                    status = response.status if response else None
                    html = page.content()
                finally:
                    browser.close()
        except Exception as exc:
            msg = str(exc)
            if "Executable doesn't exist" in msg or "playwright install" in msg:
                log.error("Chromium not installed. Run: playwright install chromium")
            else:
                log.warning("Dynamic fetch failed for %s: %s", url, exc)
            return []

        clean = trafilatura.extract(html, include_comments=False) or ""
        hash_basis = clean if clean.strip() else html
        chash = content_hash(hash_basis)
        return [
            RawPage(
                id=make_page_id(url, chash),
                competitor_id=competitor_id,
                url=url,
                source_type=SourceType.DYNAMIC,
                raw_html=html,
                clean_text=clean or None,
                http_status=status,
                content_hash=chash,
                fetched_at=utcnow(),
            )
        ]
