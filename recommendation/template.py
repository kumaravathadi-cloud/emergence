"""Memo template: call, rationale, falsifiers, cited sources — skimmable in <60s.

A pure rendering function so its output is directly testable without touching
the LLM or the filesystem.
"""

from __future__ import annotations

from typing import Any

from analysis.score import RUBRIC_WEIGHTS

_SECTION_LABELS: dict[str, tuple[str, str]] = {
    "product_fit": ("Product fit", "product"),
    "team_execution": ("Team & execution", "team"),
    "market_timing": ("Market & timing", "market"),
    "traction": ("Traction", "traction"),
    "differentiation": ("Differentiation", "differentiation"),
}


def render_memo(
    analysis: dict[str, Any],
    *,
    call: str,
    call_note: str,
    falsifiers: list[str],
) -> str:
    score = analysis["score"]
    lines = [
        f"# {analysis['candidate_name']}",
        "",
        f"**Call: {call}**  ",
        f"Score: {score['total']}/100 — {call_note}",
        "",
    ]

    if analysis["confidence"] == "low":
        reasons = ", ".join(analysis["flags"]) or "thin source data"
        lines += [f"> ⚠️ Low confidence: {reasons}.", ""]

    lines += ["## Rationale", ""]
    for category, (label, section_key) in _SECTION_LABELS.items():
        section = analysis[section_key]
        lines.append(
            f"**{label}** ({score[category]}/{RUBRIC_WEIGHTS[category]}): {section['summary']}"
        )
        lines.append("")

    lines += [f"**Risks**: {analysis['risks']['summary']}", ""]

    lines += ["## What would change this call", ""]
    for i, falsifier in enumerate(falsifiers, start=1):
        lines.append(f"{i}. {falsifier}")
    lines.append("")

    citations = []
    for _, section_key in _SECTION_LABELS.values():
        citations += analysis[section_key]["citations"]
    citations += analysis["risks"]["citations"]
    citations.append(analysis["source_url"])
    seen: set[str] = set()
    unique_citations = [c for c in citations if c and not (c in seen or seen.add(c))]

    lines += ["## Sources", ""]
    lines += [f"- {url}" for url in unique_citations]
    lines.append("")

    return "\n".join(lines)
