"""Signals and changes feeds (filterable, paginated)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from pipeline.schemas import SignalType

from api import repository as repo
from api.db import ApiDB
from api.deps import get_db
from api.schemas import Change, Page, Signal

router = APIRouter(tags=["feeds"])


@router.get("/signals", response_model=Page[Signal])
def list_signals(
    db: ApiDB = Depends(get_db),
    competitor: str | None = Query(default=None),
    signal_type: SignalType | None = Query(default=None),
    min_significance: int | None = Query(default=None, ge=1, le=5),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Page:
    items, total = repo.list_signals(
        db,
        competitor=competitor,
        signal_type=signal_type.value if signal_type else None,
        min_significance=min_significance,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/changes", response_model=Page[Change])
def list_changes(
    db: ApiDB = Depends(get_db),
    competitor: str | None = Query(default=None),
    signal_type: SignalType | None = Query(default=None),
    min_significance: int | None = Query(default=None, ge=1, le=5),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Page:
    items, total = repo.list_changes(
        db,
        competitor=competitor,
        signal_type=signal_type.value if signal_type else None,
        min_significance=min_significance,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    return Page(items=items, total=total, limit=limit, offset=offset)
