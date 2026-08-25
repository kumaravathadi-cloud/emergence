"""CLI: `sourcing run --topic "..."` -> writes data/raw/<run_id>/candidates.json.

Fetch and normalize are wrapped so one source failing (retries exhausted) or one
thin candidate never stops the run — see SYSTEM_DESIGN.md > Reliability.
"""

from __future__ import annotations

import argparse
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator

from common.logging import get_run_logger, log_event
from common.retry import RetryExhausted
from sourcing.fetch import fetch_hn_show_posts, fetch_yc_companies, fetch_yc_founders
from sourcing.normalize import normalize_hn, normalize_yc

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "candidate.v1.json"
DATA_DIR = Path("data") / "raw"


def new_run_id() -> str:
    return f"{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"


def _load_validator() -> Draft7Validator:
    return Draft7Validator(json.loads(SCHEMA_PATH.read_text()))


def _source_yc(
    topic: str, hits_per_page: int, run_id: str, logger, validator
) -> list[dict[str, Any]]:
    try:
        hits = fetch_yc_companies(topic, hits_per_page=hits_per_page)
    except RetryExhausted as exc:
        log_event(
            logger,
            stage="sourcing",
            candidate="__yc_search__",
            status="retry_exhausted",
            error=str(exc),
        )
        return []

    candidates = []
    for hit in hits:
        slug = hit.get("slug")
        founders: list[dict[str, Any]] = []
        if slug:
            try:
                founders = fetch_yc_founders(slug)
            except RetryExhausted as exc:
                log_event(
                    logger,
                    stage="sourcing",
                    candidate=hit.get("name", slug),
                    status="retry_exhausted",
                    detail="founders",
                    error=str(exc),
                )
        candidate = normalize_yc(hit, founders, run_id)
        validator.validate(candidate)
        candidates.append(candidate)
        log_event(
            logger,
            stage="sourcing",
            candidate=candidate["name"],
            status="flagged_low_data" if candidate["low_data"] else "ok",
            source="yc",
        )
    return candidates


def _source_hn(
    topic: str, hits_per_page: int, run_id: str, logger, validator
) -> list[dict[str, Any]]:
    try:
        hits = fetch_hn_show_posts(topic, hits_per_page=hits_per_page)
    except RetryExhausted as exc:
        log_event(
            logger,
            stage="sourcing",
            candidate="__hn_search__",
            status="retry_exhausted",
            error=str(exc),
        )
        return []

    candidates = []
    for hit in hits:
        candidate = normalize_hn(hit, run_id)
        validator.validate(candidate)
        candidates.append(candidate)
        log_event(
            logger,
            stage="sourcing",
            candidate=candidate["name"],
            status="flagged_low_data" if candidate["low_data"] else "ok",
            source="hacker_news",
        )
    return candidates


def run(topic: str, *, run_id: str | None = None, hits_per_page: int = 20) -> Path:
    run_id = run_id or new_run_id()
    logger = get_run_logger(run_id)
    validator = _load_validator()

    candidates = _source_yc(topic, hits_per_page, run_id, logger, validator)
    candidates += _source_hn(topic, hits_per_page, run_id, logger, validator)

    out_dir = DATA_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "candidates.json"
    out_path.write_text(json.dumps(candidates, indent=2))
    return out_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="sourcing")
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="Source candidates for a topic.")
    run_parser.add_argument("--topic", required=True)
    run_parser.add_argument(
        "--run-id", default=None, help="Reuse an existing run_id instead of generating one."
    )
    run_parser.add_argument("--hits-per-page", type=int, default=20)

    args = parser.parse_args(argv)
    if args.command == "run":
        out_path = run(args.topic, run_id=args.run_id, hits_per_page=args.hits_per_page)
        print(out_path)


if __name__ == "__main__":
    main()
