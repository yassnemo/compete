"""Shared Pydantic schemas and enums for the compete pipeline.

These types are the contract between collection, extraction, storage, and the
API. The `Signal` model is the structured-output target enforced via
`instructor` in the extraction layer (Phase 2).
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl, field_validator


class SignalType(StrEnum):
    """Canonical signal taxonomy used everywhere (DB, API, UI badges)."""

    PRICING_CHANGE = "pricing_change"
    PRODUCT_LAUNCH = "product_launch"
    BLOG_POST = "blog_post"
    PRESS_RELEASE = "press_release"
    JOB_POSTING = "job_posting"
    LEADERSHIP_CHANGE = "leadership_change"
    FUNDING_NEWS = "funding_news"
    OTHER = "other"


class SourceType(StrEnum):
    """How a tracked URL should be collected."""

    STATIC = "static"
    DYNAMIC = "dynamic"
    RSS = "rss"
    JOBS = "jobs"


class ChangeType(StrEnum):
    NEW = "new"
    UPDATED = "updated"
    REMOVED = "removed"


def utcnow() -> datetime:
    """Timezone-aware UTC now (avoids naive-datetime footguns in DuckDB)."""
    return datetime.now(UTC)


# --------------------------------------------------------------------------- #
# Extraction target - enforced by instructor in Phase 2.
# --------------------------------------------------------------------------- #
class Signal(BaseModel):
    """A single competitive-intelligence signal extracted from content.

    This is the strict schema the LLM must produce. On validation failure the
    extraction layer retries once, feeding the validation error back.
    """

    signal_type: SignalType = Field(description="The kind of signal this content represents.")
    title: str = Field(min_length=1, max_length=300, description="Short headline.")
    summary: str = Field(
        max_length=600,
        description="At most two sentences summarizing the signal.",
    )
    entities: list[str] = Field(
        default_factory=list,
        description="Products, people, or organizations mentioned.",
    )
    significance: int = Field(
        ge=1, le=5, description="Model's estimate of importance (1=trivial, 5=major)."
    )
    confidence: float = Field(ge=0.0, le=1.0, description="Model's confidence in this extraction.")

    @field_validator("entities")
    @classmethod
    def _dedupe_entities(cls, v: list[str]) -> list[str]:
        seen: dict[str, None] = {}
        for e in v:
            e = e.strip()
            if e:
                seen.setdefault(e, None)
        return list(seen.keys())


# --------------------------------------------------------------------------- #
# Config models (loaded from config/competitors.yaml).
# --------------------------------------------------------------------------- #
class TrackedURL(BaseModel):
    url: HttpUrl
    source_type: SourceType = SourceType.STATIC
    signal_hint: SignalType | None = Field(
        default=None,
        description="Optional hint to bias extraction for this URL.",
    )


class CompetitorConfig(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$")
    name: str
    domain: str
    industry: str | None = None
    tier: int = Field(default=2, ge=1, le=3)
    tracked_urls: list[TrackedURL] = Field(default_factory=list)


class CollectionDefaults(BaseModel):
    throttle_seconds: float = 2.0
    respect_robots: bool = True


class CompetitorsFile(BaseModel):
    defaults: CollectionDefaults = Field(default_factory=CollectionDefaults)
    competitors: list[CompetitorConfig] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Storage row models.
# --------------------------------------------------------------------------- #
class RawPage(BaseModel):
    """A single fetched snapshot of a tracked URL (the `raw_pages` row)."""

    id: str
    competitor_id: str
    url: str
    source_type: SourceType
    raw_html: str
    fetched_at: datetime = Field(default_factory=utcnow)
    content_hash: str
    # Cleaned/extracted main text (trafilatura); optional at fetch time.
    clean_text: str | None = None
    http_status: int | None = None
