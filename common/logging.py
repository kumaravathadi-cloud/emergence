"""Structured per-run logger: one JSON line per candidate per stage.

Writes to logs/<run_id>.log so a run can be traced end-to-end afterward
without re-running anything (see SYSTEM_DESIGN.md > Maintainability).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

LOGS_DIR = Path("logs")


class _JsonLineFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = getattr(record, "event", None)
        if payload is None:
            payload = {"message": record.getMessage()}
        payload = {"ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"), **payload}
        return json.dumps(payload, default=str)


def get_run_logger(run_id: str) -> logging.Logger:
    """Return a logger that appends structured JSON lines to logs/<run_id>.log."""
    logger = logging.getLogger(f"run.{run_id}")
    if logger.handlers:
        return logger

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(LOGS_DIR / f"{run_id}.log", encoding="utf-8")
    handler.setFormatter(_JsonLineFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


def log_event(
    logger: logging.Logger,
    *,
    stage: str,
    candidate: str,
    status: str,
    **fields: Any,
) -> None:
    """Log one structured line for a single candidate at a single stage.

    status is a short outcome tag, e.g. "ok", "flagged_low_data",
    "flagged_low_confidence", "retry_exhausted".
    """
    logger.info(
        "",
        extra={"event": {"stage": stage, "candidate": candidate, "status": status, **fields}},
    )
