"""Quick read-only inspection of the dbt marts (Phase 3 verification)."""

from __future__ import annotations

import duckdb
from pipeline.config import get_settings

con = duckdb.connect(str(get_settings().duckdb_path), read_only=True)

counts = [
    "dim_competitors",
    "fct_changes",
    "fct_hiring",
    "fct_pricing_history",
    "agg_weekly_competitor",
    "fct_signal_duplicates",
]
print("=== mart row counts ===")
for t in counts:
    n = con.execute(f"select count(*) from main_marts.{t}").fetchone()[0]
    print(f"  {t:26} {n:>6}")

print("\n=== sample fct_hiring (parsed role/location) ===")
for r in con.execute(
    "select competitor_id, role, location from main_marts.fct_hiring "
    "where location is not null limit 4"
).fetchall():
    print("  ", r)

print("\n=== agg_weekly_competitor (top 4 by total_changes) ===")
for r in con.execute(
    "select competitor_id, week, total_changes, high_significance_changes, avg_significance "
    "from main_marts.agg_weekly_competitor order by total_changes desc limit 4"
).fetchall():
    print("  ", r)

print("\n=== fct_signal_duplicates (sample) ===")
for r in con.execute(
    "select competitor_id, signal_type, round(similarity,3) "
    "from main_marts.fct_signal_duplicates order by similarity desc limit 4"
).fetchall():
    print("  ", r)

con.close()
