"""Run the dbt build (staging → marts → tests) programmatically.

Used by `run-all` and the demo seeder so the marts are materialized after the
raw layer changes. dbt is an optional extra (`uv sync --extra dbt`).
"""

from __future__ import annotations

import os

from pipeline.config import REPO_ROOT, Settings, get_settings
from pipeline.logging_setup import get_logger

log = get_logger(__name__)


def build_marts(settings: Settings | None = None) -> bool:
    """Invoke `dbt build` against the configured warehouse. Returns success."""
    s = settings or get_settings()
    try:
        from dbt.cli.main import dbtRunner
    except ImportError:
        log.error("dbt not installed. Run: uv sync --extra dbt")
        return False

    os.environ["COMPETE_DUCKDB_PATH"] = str(s.duckdb_path)
    project = str(REPO_ROOT / "warehouse" / "dbt")
    result = dbtRunner().invoke(["build", "--project-dir", project, "--profiles-dir", project])
    return bool(result.success)
