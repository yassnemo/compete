"""compete CLI - pipeline entrypoints.

Phase 0 commands prove the end-to-end loop: fetch -> store -> query.
Later phases add `extract`, `detect`, `report`, and `run-all`.
"""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.table import Table

from pipeline.collect.dispatch import collect_all
from pipeline.config import get_settings, load_competitors
from pipeline.logging_setup import force_utf8, get_logger
from pipeline.storage.duckdb_store import Warehouse

# Windows consoles default to cp1252 and choke on the UTF-8 glyphs we print.
force_utf8()

app = typer.Typer(
    name="compete",
    help="Competitive Intelligence Platform pipeline.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()
log = get_logger("compete.cli")


@app.command("init-db")
def init_db() -> None:
    """Initialize the DuckDB warehouse and raw-layer schema."""
    settings = get_settings()
    settings.ensure_dirs()
    wh = Warehouse.from_settings(settings)
    console.print(f"[green]✓[/] Warehouse ready at [bold]{settings.duckdb_path}[/]")
    console.print(f"  raw_pages rows: {wh.count_raw_pages()}")
    wh.close()


@app.command("sync-competitors")
def sync_competitors() -> None:
    """Mirror competitors.yaml into the warehouse `raw.competitors` table."""
    settings = get_settings()
    settings.ensure_dirs()
    cfg = load_competitors()
    wh = Warehouse.from_settings(settings)
    for c in cfg.competitors:
        urls_json = json.dumps([t.model_dump(mode="json") for t in c.tracked_urls])
        wh.upsert_competitor(c.id, c.name, c.domain, c.industry, c.tier, urls_json)
    console.print(f"[green]✓[/] Synced {len(cfg.competitors)} competitor(s) to warehouse.")
    wh.close()


@app.command("collect")
def collect(
    competitor: str = typer.Option(
        None, "--competitor", "-c", help="Only collect this competitor id."
    ),
    limit: int = typer.Option(0, "--limit", "-n", help="Max URLs to fetch (0 = all)."),
) -> None:
    """Fetch all tracked URLs (static/dynamic/rss/jobs) and store snapshots.

    Persists each snapshot to both the DuckDB warehouse (raw.raw_pages) and the
    partitioned Parquet landing zone under data/raw/.
    """
    settings = get_settings()
    console.print("[dim]Collecting tracked URLs (fetches logged below)…[/]")
    counts = collect_all(settings, competitor=competitor, limit=limit)
    console.print(
        f"\n[bold]Done.[/] urls={counts['urls']} "
        f"[green]snapshots={counts['snapshots']}[/] [red]failed={counts['failed']}[/]"
    )


@app.command("detect")
def detect() -> None:
    """Dry run: show change candidates that WOULD be extracted (no LLM calls)."""
    from collections import Counter

    from pipeline.extract.runner import run_detection

    settings = get_settings()
    settings.ensure_dirs()
    candidates = run_detection(settings)
    counts = Counter(str(c.change_type) for c in candidates)
    console.print(
        f"[bold]{len(candidates)}[/] change candidate(s): "
        + ", ".join(f"{k}={v}" for k, v in counts.items())
        + (" (none)" if not candidates else "")
    )
    for c in candidates[:15]:
        sim = f" sim={c.similarity:.2f}" if c.similarity is not None else ""
        console.print(f"  [magenta]{c.change_type}[/] [cyan]{c.competitor_id}[/] {c.url}{sim}")
    if len(candidates) > 15:
        console.print(f"  … and {len(candidates) - 15} more")


@app.command("extract")
def extract(
    limit: int = typer.Option(0, "--limit", "-n", help="Max candidates to extract (0 = all)."),
    provider: str = typer.Option(
        None, "--provider", "-p", help="Override LLM provider (gemini|groq|ollama|mock)."
    ),
) -> None:
    """Extract structured signals from detected changes via the LLM."""
    from pipeline.extract.runner import run_extraction

    settings = get_settings()
    settings.ensure_dirs()
    console.print(
        f"[dim]provider={provider or settings.llm_provider} "
        f"embed={settings.embed_provider} threshold={settings.diff_similarity_threshold}[/]"
    )
    stats = run_extraction(limit=limit, provider_override=provider, settings=settings)
    console.print(
        f"\n[bold]Extraction done.[/] provider={stats.provider} model={stats.model}\n"
        f"  candidates={stats.candidates} considered={stats.considered} "
        f"[green]extracted={stats.extracted}[/] [red]failed={stats.failed}[/] "
        f"tokens={stats.total_tokens}"
    )
    if stats.by_type:
        console.print("  by type: " + ", ".join(f"{k}={v}" for k, v in stats.by_type.items()))


@app.command("run-all")
def run_all(
    provider: str = typer.Option(None, "--provider", "-p", help="Override LLM provider."),
    limit: int = typer.Option(0, "--limit", "-n", help="Max URLs/candidates per step."),
) -> None:
    """Full pipeline: sync → collect → extract → transform → report. Cron/CI-friendly."""
    from pipeline.extract.runner import run_extraction
    from pipeline.report.generate import build_weekly_report
    from pipeline.transform import build_marts

    settings = get_settings()
    settings.ensure_dirs()

    console.print("[bold cyan]1/5 sync competitors[/]")
    cfg = load_competitors()
    wh = Warehouse.from_settings(settings)
    for c in cfg.competitors:
        urls_json = json.dumps([t.model_dump(mode="json") for t in c.tracked_urls])
        wh.upsert_competitor(c.id, c.name, c.domain, c.industry, c.tier, urls_json)
    wh.close()
    console.print(f"  synced {len(cfg.competitors)} competitor(s)")

    console.print("[bold cyan]2/5 collect[/]")
    counts = collect_all(settings, limit=limit)
    console.print(
        f"  urls={counts['urls']} snapshots={counts['snapshots']} failed={counts['failed']}"
    )

    console.print("[bold cyan]3/5 extract[/]")
    stats = run_extraction(limit=limit, provider_override=provider, settings=settings)
    console.print(
        f"  provider={stats.provider} extracted={stats.extracted} "
        f"failed={stats.failed} tokens={stats.total_tokens}"
    )

    console.print("[bold cyan]4/5 transform (dbt build)[/]")
    ok = build_marts(settings)
    console.print(f"  dbt build: {'OK' if ok else 'FAILED'}")

    console.print("[bold cyan]5/5 report[/]")
    result = build_weekly_report(settings)
    console.print(f"  generated {result.report_id}")
    console.print("\n[green]✓ run-all complete.[/]")


@app.command("report")
def report() -> None:
    """Generate the weekly competitive brief and store it."""
    from pipeline.report.generate import build_weekly_report

    settings = get_settings()
    result = build_weekly_report(settings)
    console.print(
        f"[green]✓[/] Generated [bold]{result.report_id}[/] "
        f"([dim]{len(result.body_md)} chars[/])"
    )
    console.print(f"  summary: {result.summary[:120]}…")


@app.command("alert-test")
def alert_test() -> None:
    """Send a sample alert (dry-run unless a channel + alerts are configured)."""
    from pipeline.report.alerts import AlertItem, notify

    settings = get_settings()
    sample = [
        AlertItem(
            "Anthropic", "product_launch", "Claude Opus 4.8 released", 5, "https://anthropic.com"
        ),
        AlertItem("OpenAI", "pricing_change", "API price cut", 4, None),
    ]
    result = notify(sample, settings)
    console.print(f"[bold]Alert dispatch:[/] {result}")


@app.command("status")
def status() -> None:
    """Show what's in the warehouse (raw pages, signals, changes, LLM cost)."""
    settings = get_settings()
    if not settings.duckdb_path.exists():
        console.print("[yellow]No warehouse yet.[/] Run [bold]compete init-db[/] first.")
        raise typer.Exit(code=0)
    wh = Warehouse.from_settings(settings, read_only=True)

    summary = Table(title="warehouse summary", show_header=False)
    summary.add_column("metric", style="cyan")
    summary.add_column("value", style="bold")
    summary.add_row("raw_pages", str(wh.count("raw_pages")))
    summary.add_row("signals", str(wh.count("signals")))
    summary.add_row("changes", str(wh.count("changes")))
    summary.add_row("llm_calls", str(wh.count("llm_calls")))
    tok = wh.query("SELECT coalesce(sum(total_tokens),0) FROM raw.llm_calls")
    summary.add_row("llm_tokens (total)", str(int(tok[0][0]) if tok else 0))
    console.print(summary)

    if wh.count("signals"):
        table = Table(title="raw.signals (latest 15)", show_lines=False)
        table.add_column("competitor", style="cyan")
        table.add_column("type", style="magenta")
        table.add_column("sig", style="yellow")
        table.add_column("title", style="white", overflow="fold")
        rows = wh.query(
            """
            SELECT competitor_id, signal_type, significance, title
            FROM raw.signals ORDER BY extracted_at DESC LIMIT 15
            """
        )
        for r in rows:
            table.add_row(str(r[0]), str(r[1]), str(r[2]), str(r[3]))
        console.print(table)
    wh.close()


if __name__ == "__main__":
    app()
