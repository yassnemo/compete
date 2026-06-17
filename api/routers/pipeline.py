"""Dev/demo endpoint to trigger a pipeline extraction run."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks
from pipeline.logging_setup import get_logger

from api.schemas import PipelineRunRequest, PipelineRunResponse

router = APIRouter(prefix="/pipeline", tags=["pipeline"])
log = get_logger("api.pipeline")


def _run(provider: str | None, limit: int) -> None:
    # Imported lazily so the API starts even if extraction deps are absent.
    from pipeline.extract.runner import run_extraction

    try:
        stats = run_extraction(limit=limit, provider_override=provider)
        log.info("pipeline run complete: extracted=%d failed=%d", stats.extracted, stats.failed)
    except Exception as exc:
        log.error("pipeline run failed: %s", exc)


@router.post("/run", response_model=PipelineRunResponse, status_code=202)
def run_pipeline(body: PipelineRunRequest, background: BackgroundTasks) -> PipelineRunResponse:
    """Kick off detect→extract in the background (does not re-collect pages)."""
    background.add_task(_run, body.provider, body.limit)
    return PipelineRunResponse(
        status="accepted",
        detail="Extraction started in the background. Poll /stats/overview for updated counts.",
    )
