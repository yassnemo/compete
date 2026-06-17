"""Typed request/response models for the API (drive the OpenAPI schema)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Generic, TypeVar

from pipeline.schemas import SignalType, SourceType
from pydantic import BaseModel, Field

T = TypeVar("T")


# ------------------------------- envelopes -------------------------------- #
class Page(BaseModel, Generic[T]):
    """Standard paginated envelope."""

    items: list[T]
    total: int
    limit: int
    offset: int


class ErrorBody(BaseModel):
    type: str
    message: str


class ErrorEnvelope(BaseModel):
    error: ErrorBody


# ------------------------------ competitors ------------------------------- #
class TrackedURLModel(BaseModel):
    url: str
    source_type: SourceType = SourceType.STATIC
    signal_hint: SignalType | None = None


class CompetitorBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    domain: str | None = None
    industry: str | None = None
    tier: int = Field(default=2, ge=1, le=3)
    tracked_urls: list[TrackedURLModel] = Field(default_factory=list)


class CompetitorCreate(CompetitorBase):
    id: str | None = Field(default=None, description="Slug; derived from name if omitted.")


class CompetitorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    domain: str | None = None
    industry: str | None = None
    tier: int | None = Field(default=None, ge=1, le=3)
    tracked_urls: list[TrackedURLModel] | None = None


class Competitor(CompetitorBase):
    id: str
    tracked_url_count: int = 0
    signal_count: int = 0
    high_significance_count: int = 0
    last_signal_at: datetime | None = None


# -------------------------------- signals --------------------------------- #
class Signal(BaseModel):
    signal_id: str
    competitor_id: str
    url: str | None = None
    signal_type: SignalType
    title: str | None = None
    summary: str | None = None
    entities: list[str] = Field(default_factory=list)
    significance: int | None = None
    confidence: float | None = None
    extracted_at: datetime | None = None


# -------------------------------- changes --------------------------------- #
class Change(BaseModel):
    change_id: str
    competitor_id: str
    url: str | None = None
    change_type: str
    signal_type: SignalType | None = None
    title: str | None = None
    summary: str | None = None
    significance_score: int | None = None
    weighted_significance: int | None = None
    confidence: float | None = None
    detected_at: datetime | None = None


# ------------------------------- analytics -------------------------------- #
class PricingPoint(BaseModel):
    competitor_id: str
    plan: str
    price: float
    currency: str | None = None
    captured_at: datetime | None = None


class HiringRow(BaseModel):
    competitor_id: str
    role: str
    location: str | None = None
    posted_at: datetime | None = None
    removed_at: datetime | None = None


class CadencePoint(BaseModel):
    week: date
    count: int


class TrendPoint(BaseModel):
    week: date
    total_changes: int
    high_significance_changes: int


class TypeCount(BaseModel):
    signal_type: SignalType
    count: int


class OverviewStats(BaseModel):
    competitors_tracked: int
    signals_total: int
    signals_this_week: int
    high_significance_count: int
    active_alerts: int
    changes_this_week: int
    by_type: list[TypeCount]
    weekly_trend: list[TrendPoint]


# -------------------------------- reports --------------------------------- #
class ReportSummary(BaseModel):
    id: str
    title: str
    week_start: date | None = None
    summary: str | None = None
    created_at: datetime | None = None


class Report(ReportSummary):
    body_md: str | None = None


# -------------------------------- pipeline -------------------------------- #
class PipelineRunRequest(BaseModel):
    provider: str | None = Field(default=None, description="Override LLM provider.")
    limit: int = Field(default=0, ge=0, description="Max candidates to extract (0 = all).")


class PipelineRunResponse(BaseModel):
    status: str
    detail: str
