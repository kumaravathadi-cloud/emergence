"""Structured-extract + scoring prompt for one candidate, read against thesis.md.

thesis.md is read directly (not copied in here) so the thesis stays a single
source of truth, per SYSTEM_DESIGN.md.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

THESIS_PATH = Path(__file__).resolve().parent.parent / "thesis.md"

_SYSTEM_PROMPT = (
    "You are a VC analyst assistant. You extract structured facts about a candidate "
    "company and judge its fit against a fixed investment thesis. Every claim you make "
    "must be traceable to the candidate data you were given — never invent facts, "
    "funding, metrics, or team history that isn't present in that data. If the data is "
    "too thin to support a claim, say so in the summary instead of guessing."
)

_RESPONSE_SHAPE = {
    "team": {"summary": "string", "citations": ["string, a URL from the candidate data"]},
    "product": {"summary": "string", "citations": ["string"]},
    "market": {"summary": "string", "citations": ["string"]},
    "traction": {"summary": "string", "citations": ["string"]},
    "risks": {"summary": "string", "citations": ["string"]},
    "differentiation": {"summary": "string", "citations": ["string"]},
    "fit_scores": {
        "product_fit": "float 0.0-1.0",
        "team_execution": "float 0.0-1.0",
        "market_timing": "float 0.0-1.0",
        "traction": "float 0.0-1.0",
        "differentiation": "float 0.0-1.0",
    },
}


def load_thesis(path: Path = THESIS_PATH) -> str:
    return path.read_text()


def build_messages(
    candidate: dict[str, Any],
    thesis_text: str,
    *,
    validation_error: str | None = None,
) -> list[dict[str, str]]:
    """Build the chat messages for one candidate's structured-extract + scoring call.

    fit_scores are 0.0-1.0 judgments of category fit; score.py — not the LLM —
    applies the thesis's point weights to turn those into the 0-100 score, so the
    weighting itself stays a deterministic, testable calculation.
    """
    user = f"""THESIS:
{thesis_text}

CANDIDATE DATA (the only source of facts you may cite):
{json.dumps(candidate, indent=2)}

Return a json object with exactly this shape:
{json.dumps(_RESPONSE_SHAPE, indent=2)}

Rules:
- Every citation must be a URL taken from the candidate data above (site or source_url).
- The traction section must be grounded in the candidate's `signal` field (its YC
  batch recency or its HN points) — say plainly if that's the only traction evidence
  available, rather than inferring traction from unrelated data.
- fit_scores are 0.0-1.0 judgments of how well the candidate fits each thesis rubric
  category, not point totals — score.py applies the point weights separately.
- If candidate data is too thin to judge a category confidently, still return a score,
  but say so plainly in that section's summary rather than inventing detail.
- Return only the json object, no prose outside it."""

    if validation_error:
        user += (
            "\n\nYour previous response failed json schema validation with this error — "
            f"fix it and return a corrected json object:\n{validation_error}"
        )

    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]
