"""Competitor CRUD endpoints."""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException

from api import repository as repo
from api.db import ApiDB
from api.deps import get_db
from api.schemas import Competitor, CompetitorCreate, CompetitorUpdate

router = APIRouter(prefix="/competitors", tags=["competitors"])


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "competitor"


@router.get("", response_model=list[Competitor])
def list_competitors(db: ApiDB = Depends(get_db)) -> list[dict]:
    return repo.list_competitors(db)


@router.post("", response_model=Competitor, status_code=201)
def create_competitor(body: CompetitorCreate, db: ApiDB = Depends(get_db)) -> dict:
    competitor_id = body.id or _slugify(body.name)
    if repo.get_competitor(db, competitor_id):
        raise HTTPException(status_code=409, detail=f"Competitor '{competitor_id}' already exists.")
    repo.upsert_competitor(
        db,
        competitor_id=competitor_id,
        name=body.name,
        domain=body.domain,
        industry=body.industry,
        tier=body.tier,
        tracked_urls=[t.model_dump(mode="json") for t in body.tracked_urls],
    )
    created = repo.get_competitor(db, competitor_id)
    assert created is not None
    return created


@router.get("/{competitor_id}", response_model=Competitor)
def get_competitor(competitor_id: str, db: ApiDB = Depends(get_db)) -> dict:
    found = repo.get_competitor(db, competitor_id)
    if not found:
        raise HTTPException(status_code=404, detail=f"Competitor '{competitor_id}' not found.")
    return found


@router.patch("/{competitor_id}", response_model=Competitor)
def update_competitor(
    competitor_id: str, body: CompetitorUpdate, db: ApiDB = Depends(get_db)
) -> dict:
    existing = repo.get_competitor(db, competitor_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Competitor '{competitor_id}' not found.")
    tracked = (
        [t.model_dump(mode="json") for t in body.tracked_urls]
        if body.tracked_urls is not None
        else existing["tracked_urls"]
    )
    repo.upsert_competitor(
        db,
        competitor_id=competitor_id,
        name=body.name or existing["name"],
        domain=body.domain if body.domain is not None else existing["domain"],
        industry=body.industry if body.industry is not None else existing["industry"],
        tier=body.tier if body.tier is not None else existing["tier"],
        tracked_urls=tracked,
    )
    updated = repo.get_competitor(db, competitor_id)
    assert updated is not None
    return updated


@router.delete("/{competitor_id}", status_code=204)
def delete_competitor(competitor_id: str, db: ApiDB = Depends(get_db)) -> None:
    if not repo.get_competitor(db, competitor_id):
        raise HTTPException(status_code=404, detail=f"Competitor '{competitor_id}' not found.")
    repo.delete_competitor(db, competitor_id)
