"""API tests via FastAPI TestClient against a seeded temp warehouse.

Marts are not built here (no dbt), so mart-backed endpoints should degrade
gracefully to empty results rather than error.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db = tmp_path / "api.duckdb"
    monkeypatch.setenv("COMPETE_DUCKDB_PATH", str(db))
    monkeypatch.setenv("COMPETE_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("COMPETE_LLM_PROVIDER", "mock")

    from pipeline.config import get_settings
    from pipeline.schemas import utcnow
    from pipeline.storage.duckdb_store import Warehouse

    get_settings.cache_clear()

    # Seed minimal raw data.
    wh = Warehouse(db)
    wh.upsert_competitor(
        "acme",
        "Acme",
        "acme.com",
        "SaaS",
        1,
        json.dumps(
            [{"url": "https://acme.com/blog", "source_type": "rss", "signal_hint": "blog_post"}]
        ),
    )
    wh.upsert_signal(
        signal_id="sig1",
        competitor_id="acme",
        url="https://acme.com/news/launch",
        signal_type="product_launch",
        title="Acme 2.0 launched",
        summary="Big launch.",
        entities_json='["Acme 2.0"]',
        significance=5,
        confidence=0.9,
        embedding=[0.1, 0.2],
        source_hash="h1",
        model="seed",
        extracted_at=utcnow(),
    )
    wh.close()

    from api.main import app
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c

    get_settings.cache_clear()


def test_health(client) -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_list_competitors(client) -> None:
    r = client.get("/competitors")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["id"] == "acme"
    assert data[0]["signal_count"] == 1
    assert data[0]["tracked_url_count"] == 1


def test_signals_paginated_and_filtered(client) -> None:
    r = client.get("/signals", params={"limit": 10})
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["signal_type"] == "product_launch"
    assert body["items"][0]["entities"] == ["Acme 2.0"]
    # filter that excludes everything
    empty = client.get("/signals", params={"signal_type": "funding_news"}).json()
    assert empty["total"] == 0


def test_changes_endpoint_graceful_without_marts(client) -> None:
    # fct_changes mart doesn't exist in this temp db -> empty, not 500.
    r = client.get("/changes")
    assert r.status_code == 200
    assert r.json() == {"items": [], "total": 0, "limit": 50, "offset": 0}


def test_overview_graceful(client) -> None:
    r = client.get("/stats/overview")
    assert r.status_code == 200
    body = r.json()
    assert body["competitors_tracked"] == 1
    assert body["signals_total"] == 1


def test_crud_roundtrip(client) -> None:
    created = client.post(
        "/competitors",
        json={"name": "New Co", "domain": "new.co", "tier": 2, "tracked_urls": []},
    )
    assert created.status_code == 201
    assert created.json()["id"] == "new-co"

    # duplicate -> 409 with error envelope
    dup = client.post("/competitors", json={"name": "New Co"})
    assert dup.status_code == 409
    assert dup.json()["error"]["type"] == "http_error"

    patched = client.patch("/competitors/new-co", json={"tier": 1})
    assert patched.json()["tier"] == 1

    assert client.delete("/competitors/new-co").status_code == 204
    assert client.get("/competitors/new-co").status_code == 404


def test_404_error_envelope(client) -> None:
    r = client.get("/competitors/nope")
    assert r.status_code == 404
    assert r.json() == {"error": {"type": "http_error", "message": "Competitor 'nope' not found."}}
