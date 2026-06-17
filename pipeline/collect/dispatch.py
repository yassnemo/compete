"""Source-type dispatch: route a tracked URL to the right collector.

Collectors are instantiated once and reused (they hold robots/throttle caches).
All collectors share the contract ``collect(competitor_id, url) -> list[RawPage]``.
"""

from __future__ import annotations

from pipeline.collect.base import Collector
from pipeline.collect.dynamic import DynamicCollector
from pipeline.collect.jobs import JobsCollector
from pipeline.collect.rss import RSSCollector
from pipeline.collect.static import StaticCollector
from pipeline.config import Settings, get_settings
from pipeline.logging_setup import get_logger
from pipeline.schemas import RawPage, SourceType

log = get_logger(__name__)


class CollectorRegistry:
    """Lazily builds and caches one collector per source type."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._cache: dict[SourceType, Collector] = {}

    def get(self, source_type: SourceType) -> Collector:
        if source_type not in self._cache:
            self._cache[source_type] = self._build(source_type)
        return self._cache[source_type]

    def _build(self, source_type: SourceType) -> Collector:
        match source_type:
            case SourceType.STATIC:
                return StaticCollector(self.settings)
            case SourceType.DYNAMIC:
                return DynamicCollector(self.settings)
            case SourceType.RSS:
                return RSSCollector(self.settings)
            case SourceType.JOBS:
                return JobsCollector(self.settings)
        raise ValueError(f"Unknown source_type: {source_type}")

    def collect(self, competitor_id: str, url: str, source_type: SourceType) -> list[RawPage]:
        collector = self.get(source_type)
        return collector.collect(competitor_id, url)


def collect_all(
    settings: Settings | None = None,
    competitor: str | None = None,
    limit: int = 0,
) -> dict[str, int]:
    """Collect all tracked URLs into DuckDB + Parquet. Returns run counts.

    Shared by the `collect` CLI command and `run-all`. Never raises on a single
    URL failure - collectors are defensive and failures are counted.
    """
    from pipeline.config import get_settings, load_competitors
    from pipeline.storage.duckdb_store import Warehouse
    from pipeline.storage.parquet_store import write_raw_pages

    s = settings or get_settings()
    s.ensure_dirs()
    cfg = load_competitors()
    registry = CollectorRegistry(s)
    wh = Warehouse.from_settings(s)
    counts = {"urls": 0, "snapshots": 0, "failed": 0}
    all_pages: list[RawPage] = []
    try:
        for comp in cfg.competitors:
            if competitor and comp.id != competitor:
                continue
            for tracked in comp.tracked_urls:
                if limit and counts["urls"] >= limit:
                    break
                url = str(tracked.url)
                counts["urls"] += 1
                log.info("collecting %s [%s] %s", comp.id, tracked.source_type, url)
                try:
                    pages = registry.collect(comp.id, url, tracked.source_type)
                except Exception as exc:
                    log.warning("collector error for %s: %s", url, exc)
                    counts["failed"] += 1
                    continue
                if not pages:
                    counts["failed"] += 1
                    continue
                for page in pages:
                    wh.upsert_raw_page(page)
                all_pages.extend(pages)
                counts["snapshots"] += len(pages)
        write_raw_pages(all_pages, s.data_dir)
        return counts
    finally:
        wh.close()
