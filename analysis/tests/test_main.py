import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from jsonschema import Draft7Validator

from analysis.main import _assemble_record, _degraded_record, _slugify, analyze_candidate

SCHEMA = json.loads(
    (Path(__file__).resolve().parent.parent.parent / "schemas" / "analysis.v1.json").read_text()
)
VALIDATOR = Draft7Validator(SCHEMA)

CANDIDATE = {
    "schema_version": "1",
    "run_id": "run123",
    "name": "Acme AI",
    "site": "https://acme.ai",
    "one_liner": "AI agent that reconciles invoices.",
    "founders": ["Jane Doe"],
    "signal": {"source": "yc", "type": "batch", "value": "Summer 2026"},
    "source_url": "https://www.ycombinator.com/companies/acme-ai",
    "low_data": False,
    "flags": [],
}

GOOD_RAW = {
    "team": {
        "summary": "Solo technical founder.",
        "citations": ["https://www.ycombinator.com/companies/acme-ai"],
    },
    "product": {
        "summary": "Owns invoice reconciliation end to end.",
        "citations": ["https://acme.ai"],
    },
    "market": {"summary": "Common SMB workflow.", "citations": ["https://acme.ai"]},
    "risks": {
        "summary": "Early stage, unproven retention.",
        "citations": ["https://www.ycombinator.com/companies/acme-ai"],
    },
    "differentiation": {"summary": "Deep ERP integrations.", "citations": ["https://acme.ai"]},
    "fit_scores": {
        "product_fit": 0.8,
        "team_execution": 0.6,
        "market_timing": 0.7,
        "traction": 0.5,
        "differentiation": 0.4,
    },
}

# Missing "product", "market", "risks", "differentiation", "fit_scores" -> assembly fails.
MALFORMED_RAW = {"team": {"summary": "incomplete"}}


def test_assemble_record_matches_schema():
    record = _assemble_record(CANDIDATE, GOOD_RAW)

    VALIDATOR.validate(record)
    assert record["confidence"] == "high"
    assert record["score"]["total"] == pytest.approx(
        0.8 * 30 + 0.6 * 25 + 0.7 * 20 + 0.5 * 15 + 0.4 * 10
    )


def test_assemble_record_low_data_candidate_is_low_confidence():
    low_data_candidate = {**CANDIDATE, "low_data": True, "flags": ["missing_founders"]}

    record = _assemble_record(low_data_candidate, GOOD_RAW)

    assert record["confidence"] == "low"
    assert record["flags"] == ["missing_founders"]


def test_assemble_record_missing_fit_score_raises():
    bad_raw = {**GOOD_RAW, "fit_scores": {"product_fit": 0.5}}

    with pytest.raises(ValueError):
        _assemble_record(CANDIDATE, bad_raw)


def test_degraded_record_matches_schema_and_flags_reason():
    record = _degraded_record(CANDIDATE, reason="LLM call failed: boom")

    VALIDATOR.validate(record)
    assert record["confidence"] == "low"
    assert record["score"]["total"] == 0
    assert "validation_retry_failed" in record["flags"]


def test_analyze_candidate_succeeds_first_try():
    logger = MagicMock()

    with patch("analysis.main._call_llm", return_value=GOOD_RAW) as mock_call:
        record = analyze_candidate(CANDIDATE, "THESIS TEXT", VALIDATOR, logger)

    assert mock_call.call_count == 1
    assert record["confidence"] == "high"
    VALIDATOR.validate(record)


def test_analyze_candidate_degrades_after_two_failures():
    logger = MagicMock()

    with patch("analysis.main._call_llm", return_value=MALFORMED_RAW) as mock_call:
        record = analyze_candidate(CANDIDATE, "THESIS TEXT", VALIDATOR, logger)

    assert mock_call.call_count == 2
    assert record["confidence"] == "low"
    assert "validation_retry_failed" in record["flags"]
    VALIDATOR.validate(record)


def test_analyze_candidate_recovers_on_retry():
    logger = MagicMock()

    with patch("analysis.main._call_llm", side_effect=[MALFORMED_RAW, GOOD_RAW]) as mock_call:
        record = analyze_candidate(CANDIDATE, "THESIS TEXT", VALIDATOR, logger)

    assert mock_call.call_count == 2
    assert record["confidence"] == "high"


def test_slugify_dedupes_collisions():
    taken: set[str] = set()

    assert _slugify("Acme AI", taken) == "acme-ai"
    assert _slugify("Acme AI", taken) == "acme-ai-2"
    assert _slugify("Acme AI!!", taken) == "acme-ai-3"
