"""Parquet raw landing zone.

Every collected snapshot is also written to a partitioned Parquet dataset under
``<data_dir>/raw/``. This is the durable, columnar raw layer dbt/DuckDB can read
directly via ``read_parquet`` - DuckDB is the warehouse, Parquet is the landing
zone (see ADR 0001). Partitioned by competitor and capture date; each run lands
a new file, so writes never rewrite history.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from pipeline.logging_setup import get_logger
from pipeline.schemas import RawPage

log = get_logger(__name__)

_COLUMNS = [
    "id",
    "competitor_id",
    "url",
    "source_type",
    "raw_html",
    "clean_text",
    "http_status",
    "content_hash",
    "fetched_at",
    "dt",
]


def _to_table(pages: list[RawPage]) -> pa.Table:
    rows: dict[str, list] = {c: [] for c in _COLUMNS}
    for p in pages:
        rows["id"].append(p.id)
        rows["competitor_id"].append(p.competitor_id)
        rows["url"].append(p.url)
        rows["source_type"].append(str(p.source_type))
        rows["raw_html"].append(p.raw_html)
        rows["clean_text"].append(p.clean_text)
        rows["http_status"].append(p.http_status)
        rows["content_hash"].append(p.content_hash)
        rows["fetched_at"].append(p.fetched_at)
        rows["dt"].append(p.fetched_at.date().isoformat())
    return pa.table(rows)


def write_raw_pages(pages: list[RawPage], data_dir: Path) -> Path | None:
    """Append snapshots to the partitioned Parquet dataset. Returns the root."""
    if not pages:
        return None
    root = Path(data_dir) / "raw"
    root.mkdir(parents=True, exist_ok=True)
    table = _to_table(pages)
    pq.write_to_dataset(
        table,
        root_path=str(root),
        partition_cols=["competitor_id", "dt"],
        basename_template=f"part-{uuid.uuid4().hex[:12]}-{{i}}.parquet",
    )
    log.info("wrote %d snapshot(s) to parquet at %s", len(pages), root)
    return root
