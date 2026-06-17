"""Thread-safe DuckDB access for the API.

FastAPI runs sync endpoints in a threadpool, and DuckDB connections are not
thread-safe, so we serialize access through a single read-write connection
guarded by a lock. Reads tolerate missing marts (returns empty) so a fresh
warehouse (before `dbt build`) degrades gracefully instead of 500-ing.
"""

from __future__ import annotations

import contextlib
import threading
from pathlib import Path
from typing import Any

import duckdb
from pipeline.logging_setup import get_logger

log = get_logger("api.db")


class ApiDB:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()
        self.conn = duckdb.connect(str(self.path))

    def query(self, sql: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
        """Run a read query, returning rows as dicts. Empty on missing table."""
        with self._lock:
            try:
                cur = self.conn.execute(sql, params or [])
            except duckdb.CatalogException:
                log.warning("query against missing object; returning empty: %s", sql.split()[0:6])
                return []
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row, strict=True)) for row in cur.fetchall()]

    def query_one(self, sql: str, params: list[Any] | None = None) -> dict[str, Any] | None:
        rows = self.query(sql, params)
        return rows[0] if rows else None

    def scalar(self, sql: str, params: list[Any] | None = None, default: Any = 0) -> Any:
        with self._lock:
            try:
                row = self.conn.execute(sql, params or []).fetchone()
            except duckdb.CatalogException:
                return default
            return row[0] if row and row[0] is not None else default

    def execute(self, sql: str, params: list[Any] | None = None) -> None:
        """Run a write statement (raises on error - used by CRUD)."""
        with self._lock:
            self.conn.execute(sql, params or [])

    def close(self) -> None:
        with contextlib.suppress(Exception):
            self.conn.close()
