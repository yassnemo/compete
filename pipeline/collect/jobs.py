"""Job-posting collector.

Careers pages are wildly inconsistent, so we prefer the *public JSON APIs* that
the common applicant-tracking systems (ATS) expose:

* Greenhouse  -> boards-api.greenhouse.io/v1/boards/<token>/jobs
* Lever       -> api.lever.co/v0/postings/<company>
* Ashby       -> api.ashbyhq.com/posting-api/job-board/<org>

For anything else we fall back to parsing schema.org ``JobPosting`` JSON-LD
embedded in the page. Each posting becomes one RawPage keyed by its URL, so a
new or removed role is detected downstream. Structured field extraction (role,
location) happens in the LLM layer in Phase 2.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
from selectolax.parser import HTMLParser

from pipeline.collect.base import Collector, content_hash, make_page_id
from pipeline.logging_setup import get_logger
from pipeline.schemas import RawPage, SourceType, utcnow

log = get_logger(__name__)


@dataclass
class JobPosting:
    title: str
    url: str
    location: str | None
    body: str | None


def _slug_from_path(url: str) -> str | None:
    parts = [p for p in urlparse(url).path.split("/") if p]
    return parts[0] if parts else None


class JobsCollector(Collector):
    """Collect job postings via ATS APIs with a JSON-LD fallback."""

    def _get_json(self, url: str) -> object | None:
        self.throttle(url)
        try:
            resp = httpx.get(
                url,
                headers={"User-Agent": self.settings.user_agent, "Accept": "application/json"},
                timeout=self.settings.request_timeout,
                follow_redirects=True,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            log.warning("jobs API fetch failed for %s: %s", url, exc)
            return None

    def _get_html(self, url: str) -> str | None:
        self.throttle(url)
        try:
            resp = httpx.get(
                url,
                headers={"User-Agent": self.settings.user_agent},
                timeout=self.settings.request_timeout,
                follow_redirects=True,
            )
            resp.raise_for_status()
            return resp.text
        except Exception as exc:
            log.warning("jobs page fetch failed for %s: %s", url, exc)
            return None

    # ----------------------------- ATS parsers --------------------------- #
    def _greenhouse(self, url: str) -> list[JobPosting] | None:
        token = _slug_from_path(url)
        if not token:
            return None
        api = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
        data = self._get_json(api)
        if not isinstance(data, dict) or "jobs" not in data:
            return None
        out: list[JobPosting] = []
        for j in data.get("jobs", []):
            out.append(
                JobPosting(
                    title=j.get("title", "(untitled)"),
                    url=j.get("absolute_url", api),
                    location=(j.get("location") or {}).get("name"),
                    body=j.get("content"),
                )
            )
        return out

    def _lever(self, url: str) -> list[JobPosting] | None:
        company = _slug_from_path(url)
        if not company:
            return None
        api = f"https://api.lever.co/v0/postings/{company}?mode=json"
        data = self._get_json(api)
        if not isinstance(data, list):
            return None
        out: list[JobPosting] = []
        for j in data:
            cats = j.get("categories") or {}
            out.append(
                JobPosting(
                    title=j.get("text", "(untitled)"),
                    url=j.get("hostedUrl", api),
                    location=cats.get("location"),
                    body=j.get("descriptionPlain"),
                )
            )
        return out

    def _ashby(self, url: str) -> list[JobPosting] | None:
        org = _slug_from_path(url)
        if not org:
            return None
        api = f"https://api.ashbyhq.com/posting-api/job-board/{org}?includeCompensation=false"
        data = self._get_json(api)
        if not isinstance(data, dict) or "jobs" not in data:
            return None
        out: list[JobPosting] = []
        for j in data.get("jobs", []):
            out.append(
                JobPosting(
                    title=j.get("title", "(untitled)"),
                    url=j.get("jobUrl") or j.get("applyUrl") or api,
                    location=j.get("location"),
                    body=j.get("descriptionPlain") or j.get("description"),
                )
            )
        return out

    def _jsonld(self, url: str) -> list[JobPosting] | None:
        html = self._get_html(url)
        if html is None:
            return None
        return parse_jsonld_jobs(html, base_url=url)

    # ------------------------------- dispatch ---------------------------- #
    def collect(self, competitor_id: str, url: str) -> list[RawPage]:
        if not self._allowed(url):
            return []
        host = urlparse(url).netloc.lower()

        postings: list[JobPosting] | None = None
        if "greenhouse" in host:
            postings = self._greenhouse(url)
        elif "lever.co" in host:
            postings = self._lever(url)
        elif "ashby" in host:
            postings = self._ashby(url)

        if not postings:
            postings = self._jsonld(url)

        if not postings:
            log.info("jobs: no structured postings found at %s", url)
            return []

        pages: list[RawPage] = []
        for job in postings:
            loc = job.location or "-"
            text = f"{job.title} ({loc})\n\n{job.body or ''}".strip()
            chash = content_hash(f"{job.title}|{loc}")
            pages.append(
                RawPage(
                    id=make_page_id(job.url, chash),
                    competitor_id=competitor_id,
                    url=job.url,
                    source_type=SourceType.JOBS,
                    raw_html=job.body or "",
                    clean_text=text or None,
                    http_status=200,
                    content_hash=chash,
                    fetched_at=utcnow(),
                )
            )
        log.info("jobs %s -> %d postings", url, len(pages))
        return pages


_TAG_RE = re.compile(r"<[^>]+>")


def parse_jsonld_jobs(html: str, base_url: str = "") -> list[JobPosting]:
    """Extract schema.org JobPosting items from JSON-LD script blocks."""
    tree = HTMLParser(html)
    found: list[JobPosting] = []
    for node in tree.css('script[type="application/ld+json"]'):
        raw = node.text(strip=False)
        if not raw or "JobPosting" not in raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        for item in _iter_jobpostings(data):
            title = item.get("title") or "(untitled)"
            loc = _jsonld_location(item)
            desc = item.get("description")
            if isinstance(desc, str):
                desc = re.sub(r"\s+", " ", _TAG_RE.sub(" ", desc)).strip()
            link = item.get("url") or base_url
            found.append(JobPosting(title=title, url=link, location=loc, body=desc))
    return found


def _iter_jobpostings(data: object):
    if isinstance(data, list):
        for d in data:
            yield from _iter_jobpostings(d)
    elif isinstance(data, dict):
        if data.get("@type") == "JobPosting":
            yield data
        if "@graph" in data:
            yield from _iter_jobpostings(data["@graph"])


def _jsonld_location(item: dict) -> str | None:
    loc = item.get("jobLocation")
    if isinstance(loc, list):
        loc = loc[0] if loc else None
    if isinstance(loc, dict):
        addr = loc.get("address")
        if isinstance(addr, dict):
            return (
                addr.get("addressLocality")
                or addr.get("addressRegion")
                or addr.get("addressCountry")
            )
    return None
