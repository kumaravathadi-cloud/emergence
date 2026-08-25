"""CLI: `analysis run --input candidates.json` -> writes data/analysis/<run_id>/<company>.json.

Each candidate's LLM response is assembled into a full record and validated
against schemas/analysis.v1.json. A validation failure gets one retry with the
error appended to the prompt; a second failure degrades that candidate to a
flagged, low-confidence record instead of failing the run (SYSTEM_DESIGN.md >
Reliability).
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from jsonschema import Draft7Validator, ValidationError
from openai import AzureOpenAI, OpenAIError

from analysis.prompts import build_messages, load_thesis
from analysis.score import RUBRIC_WEIGHTS, compute_score
from common.logging import get_run_logger, log_event
from common.retry import RetryExhausted, call_with_retry

load_dotenv()

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "analysis.v1.json"
DATA_OUT_DIR = Path("data") / "analysis"

_PLACEHOLDER_SECTION = {
    "summary": "Insufficient or malformed model output; analysis could not be completed "
    "for this candidate.",
    "citations": [],
}

_client: AzureOpenAI | None = None


def _get_client() -> AzureOpenAI:
    global _client
    if _client is None:
        _client = AzureOpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
            azure_endpoint=os.environ["OPENAI_ENDPOINT"],
            api_version=os.environ["OPENAI_API_VERSION"],
            max_retries=0,
        )
    return _client


def _call_llm(messages: list[dict[str, str]]) -> dict[str, Any]:
    def _do() -> dict[str, Any]:
        resp = _get_client().chat.completions.create(
            model=os.environ["OPENAI_MODEL"],
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        return json.loads(resp.choices[0].message.content)

    return call_with_retry(_do, exceptions=(OpenAIError, json.JSONDecodeError))


def _assemble_record(candidate: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    score = compute_score(raw["fit_scores"])
    confidence = "low" if candidate.get("low_data") else "high"
    return {
        "schema_version": "1",
        "run_id": candidate["run_id"],
        "candidate_name": candidate["name"],
        "source_url": candidate["source_url"],
        "team": raw["team"],
        "product": raw["product"],
        "market": raw["market"],
        "risks": raw["risks"],
        "differentiation": raw["differentiation"],
        "score": score,
        "confidence": confidence,
        "flags": list(candidate.get("flags", [])),
    }


def _try_build_record(
    candidate: dict[str, Any], messages: list[dict[str, str]], validator: Draft7Validator
) -> tuple[dict[str, Any] | None, str | None]:
    try:
        raw = _call_llm(messages)
    except RetryExhausted as exc:
        return None, f"LLM call failed: {exc}"

    try:
        record = _assemble_record(candidate, raw)
    except (KeyError, TypeError, ValueError) as exc:
        return None, f"malformed LLM response: {exc}"

    try:
        validator.validate(record)
    except ValidationError as exc:
        return None, f"schema validation failed: {exc.message}"

    return record, None


def _degraded_record(candidate: dict[str, Any], reason: str) -> dict[str, Any]:
    zero_fit = dict.fromkeys(RUBRIC_WEIGHTS, 0.0)
    return {
        "schema_version": "1",
        "run_id": candidate["run_id"],
        "candidate_name": candidate["name"],
        "source_url": candidate["source_url"],
        "team": _PLACEHOLDER_SECTION,
        "product": _PLACEHOLDER_SECTION,
        "market": _PLACEHOLDER_SECTION,
        "risks": _PLACEHOLDER_SECTION,
        "differentiation": _PLACEHOLDER_SECTION,
        "score": compute_score(zero_fit),
        "confidence": "low",
        "flags": [*candidate.get("flags", []), "validation_retry_failed"],
    }


def analyze_candidate(
    candidate: dict[str, Any], thesis_text: str, validator: Draft7Validator, logger
) -> dict[str, Any]:
    messages = build_messages(candidate, thesis_text)
    record, error = _try_build_record(candidate, messages, validator)

    if record is None:
        log_event(
            logger,
            stage="analysis",
            candidate=candidate["name"],
            status="validation_retry",
            error=error,
        )
        retry_messages = build_messages(candidate, thesis_text, validation_error=error)
        record, error = _try_build_record(candidate, retry_messages, validator)

    if record is None:
        record = _degraded_record(candidate, reason=error)
        log_event(
            logger,
            stage="analysis",
            candidate=candidate["name"],
            status="flagged_low_confidence",
            error=error,
        )
    else:
        log_event(
            logger,
            stage="analysis",
            candidate=candidate["name"],
            status="ok" if record["confidence"] == "high" else "flagged_low_confidence",
            score=record["score"]["total"],
        )

    return record


def _slugify(name: str, taken: set[str]) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "candidate"
    unique = slug
    n = 2
    while unique in taken:
        unique = f"{slug}-{n}"
        n += 1
    taken.add(unique)
    return unique


def _load_validator() -> Draft7Validator:
    return Draft7Validator(json.loads(SCHEMA_PATH.read_text()))


def run(input_path: str | Path) -> Path:
    input_path = Path(input_path)
    candidates = json.loads(input_path.read_text())
    run_id = candidates[0]["run_id"] if candidates else input_path.parent.name

    logger = get_run_logger(run_id)
    validator = _load_validator()
    thesis_text = load_thesis()

    out_dir = DATA_OUT_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    taken_slugs: set[str] = set()
    for candidate in candidates:
        record = analyze_candidate(candidate, thesis_text, validator, logger)
        slug = _slugify(record["candidate_name"], taken_slugs)
        (out_dir / f"{slug}.json").write_text(json.dumps(record, indent=2))

    return out_dir


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="analysis")
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="Analyze candidates from a sourcing run.")
    run_parser.add_argument(
        "--input", required=True, help="Path to a candidates.json from sourcing."
    )

    args = parser.parse_args(argv)
    if args.command == "run":
        out_dir = run(args.input)
        print(out_dir)


if __name__ == "__main__":
    main()
