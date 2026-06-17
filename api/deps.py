"""Shared FastAPI dependencies."""

from __future__ import annotations

from fastapi import Request

from api.db import ApiDB


def get_db(request: Request) -> ApiDB:
    return request.app.state.db
