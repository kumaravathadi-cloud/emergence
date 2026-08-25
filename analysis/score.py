"""Deterministic scoring: applies thesis.md's rubric weights to the LLM's
0.0-1.0 category fit judgments. Kept separate from prompts.py/main.py so the
weighting math is a pure function, testable without an LLM.
"""

from __future__ import annotations

# Weights per thesis.md > Scoring Rubric. Sum to 100.
RUBRIC_WEIGHTS: dict[str, float] = {
    "product_fit": 30,
    "team_execution": 25,
    "market_timing": 20,
    "traction": 15,
    "differentiation": 10,
}


def compute_score(fit_scores: dict[str, float]) -> dict[str, float]:
    """fit_scores: category -> 0.0-1.0 fit judgment for every RUBRIC_WEIGHTS key.

    Returns the point breakdown per category plus "total", matching the `score`
    object in schemas/analysis.v1.json. Out-of-range fit values are clamped
    rather than rejected, since they come from an LLM's free-form judgment.
    """
    missing = RUBRIC_WEIGHTS.keys() - fit_scores.keys()
    if missing:
        raise ValueError(f"missing fit score(s) for: {sorted(missing)}")

    breakdown: dict[str, float] = {}
    for category, weight in RUBRIC_WEIGHTS.items():
        fit = max(0.0, min(1.0, float(fit_scores[category])))
        breakdown[category] = round(fit * weight, 2)

    breakdown["total"] = round(sum(breakdown.values()), 2)
    return breakdown
