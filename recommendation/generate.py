"""Turns one analysis record into a call + rationale + falsifiers, per thesis.md's
score-to-call mapping (SYSTEM_DESIGN.md > S3).

Deterministic and LLM-free: the analysis stage already did the judgment (fit
scores, cited summaries); this stage only applies the fixed mapping and picks
which rubric gaps are worth naming as falsifiers.
"""

from __future__ import annotations

from typing import Any

from analysis.score import RUBRIC_WEIGHTS

# Call boundaries per thesis.md > Call Mapping.
_MEETING_THRESHOLD = 70
_WATCH_THRESHOLD = 40

FALSIFIER_TEMPLATES: dict[str, str] = {
    "product_fit": (
        "Clearer evidence the product owns one named SMB workflow end-to-end "
        "(not just assists with it) would raise the score."
    ),
    "team_execution": (
        "Surfacing stronger team signal — prior startup/exec experience or a clear "
        "technical founder — would raise the score."
    ),
    "market_timing": (
        "A more concrete 'why now' (new model capability, regulation, or category "
        "shift) or evidence the workflow is common across many SMBs would raise the score."
    ),
    "traction": (
        "Stronger traction signal — deeper HN engagement, a more recent YC batch, "
        "funding, or usage data — would raise the score."
    ),
    "differentiation": (
        "A clearer defensible edge (proprietary data, workflow depth, integrations, "
        "distribution) would raise the score."
    ),
}


def score_to_call(total: float) -> str:
    """Pure score -> call mapping per thesis.md, ignoring confidence."""
    if total >= _MEETING_THRESHOLD:
        return "Meeting"
    if total >= _WATCH_THRESHOLD:
        return "Watch"
    return "Pass"


def determine_call(analysis: dict[str, Any]) -> tuple[str, str]:
    """Returns (call, note) — note explains how the call was reached.

    A low-confidence record defaults to Watch regardless of its raw score
    (SYSTEM_DESIGN.md > S3: "Call defaults toward Watch, confidence noted"),
    since a firm Pass or Meeting isn't warranted off thin source data.
    """
    total = analysis["score"]["total"]
    raw_call = score_to_call(total)

    if analysis["confidence"] == "low":
        reasons = ", ".join(analysis["flags"]) or "thin source data"
        return (
            "Watch",
            f"confidence flagged low ({reasons}); defaulted to Watch — raw score "
            f"{total}/100 would otherwise map to {raw_call}.",
        )

    return raw_call, f"score {total}/100 maps to {raw_call} per thesis.md's call mapping."


def top_falsifiers(analysis: dict[str, Any], n: int = 3) -> list[str]:
    """The `n` rubric categories with the largest gap between weight and points earned.

    These are the concrete "2-3 things that would change it" VISION.md asks for,
    derived from the score breakdown rather than a separate LLM call.
    """
    score = analysis["score"]
    gaps = sorted(
        ((RUBRIC_WEIGHTS[category] - score[category], category) for category in RUBRIC_WEIGHTS),
        reverse=True,
    )
    picks = [category for _, category in gaps[:n]]
    return [FALSIFIER_TEMPLATES[category] for category in picks]
