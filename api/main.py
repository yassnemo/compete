"""compete API - FastAPI app over the DuckDB marts.

Run: ``uv run uvicorn api.main:app --reload`` (or ``compete-api``).
Docs: http://127.0.0.1:8000/docs
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pipeline.config import get_settings
from pipeline.logging_setup import get_logger
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.db import ApiDB
from api.routers import analytics, competitors, pipeline, reports, signals

log = get_logger("api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    settings.ensure_dirs()
    app.state.db = ApiDB(settings.duckdb_path)
    log.info("API connected to warehouse at %s", settings.duckdb_path)
    try:
        yield
    finally:
        app.state.db.close()


app = FastAPI(
    title="compete API",
    version="0.1.0",
    description="Competitive Intelligence Platform - typed read API over the DuckDB marts.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------- consistent error envelopes ----------------------- #
def _envelope(type_: str, message: str, status: int) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"type": type_, "message": message}})


@app.exception_handler(StarletteHTTPException)
async def http_exc_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _envelope("http_error", str(exc.detail), exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exc_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return _envelope("validation_error", str(exc.errors()), 422)


@app.exception_handler(Exception)
async def unhandled_exc_handler(_: Request, exc: Exception) -> JSONResponse:
    log.exception("unhandled error")
    return _envelope("internal_error", "An unexpected error occurred.", 500)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}


for r in (competitors.router, signals.router, analytics.router, reports.router, pipeline.router):
    app.include_router(r)


def main() -> None:
    """Console entrypoint: ``compete-api``."""
    import uvicorn

    settings = get_settings()
    uvicorn.run("api.main:app", host=settings.api_host, port=settings.api_port, reload=False)


if __name__ == "__main__":
    main()
