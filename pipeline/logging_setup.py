"""Centralized logging configured with Rich for readable console output."""

from __future__ import annotations

import contextlib
import logging
import sys

from rich.logging import RichHandler

_CONFIGURED = False


def force_utf8() -> None:
    """Windows consoles default to cp1252; force UTF-8 so glyphs render."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            with contextlib.suppress(ValueError, OSError):
                reconfigure(encoding="utf-8")


def setup_logging(level: int = logging.INFO) -> None:
    """Idempotently configure root logging with a Rich handler."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    force_utf8()
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
    )
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)
