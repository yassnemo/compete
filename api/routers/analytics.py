"""Per-competitor analytics + the overview stats that power the dashboard."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api import repository as repo
from api.db import ApiDB
from api.deps import get_db
from api.schemas import CadencePoint, HiringRow, OverviewStats, PricingPoint

router = APIRouter(tags=["analytics"])


def _require_competitor(db: ApiDB, competitor_id: str) -> None:
    if not repo.get_competitor(db, competitor_id):
        raise HTTPException(status_code=404, detail=f"Competitor '{competitor_id}' not found.")


@router.get("/competitors/{competitor_id}/pricing-history", response_model=list[PricingPoint])
def pricing_history(competitor_id: str, db: ApiDB = Depends(get_db)) -> list[dict]:
    _require_competitor(db, competitor_id)
    return repo.pricing_history(db, competitor_id)


@router.get("/competitors/{competitor_id}/hiring", response_model=list[HiringRow])
def hiring(competitor_id: str, db: ApiDB = Depends(get_db)) -> list[dict]:
    _require_competitor(db, competitor_id)
    return repo.hiring(db, competitor_id)


@router.get("/competitors/{competitor_id}/cadence", response_model=list[CadencePoint])
def cadence(competitor_id: str, db: ApiDB = Depends(get_db)) -> list[dict]:
    _require_competitor(db, competitor_id)
    return repo.cadence(db, competitor_id)


@router.get("/stats/overview", response_model=OverviewStats)
def overview(db: ApiDB = Depends(get_db)) -> dict:
    return repo.overview(db)
