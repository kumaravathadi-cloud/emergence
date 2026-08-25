import pytest

from recommendation.generate import determine_call, score_to_call, top_falsifiers


@pytest.mark.parametrize(
    "total,expected",
    [
        (0, "Pass"),
        (39, "Pass"),
        (39.99, "Pass"),
        (40, "Watch"),
        (69, "Watch"),
        (69.99, "Watch"),
        (70, "Meeting"),
        (100, "Meeting"),
    ],
)
def test_score_to_call_boundaries(total, expected):
    assert score_to_call(total) == expected


def _analysis(total: float, confidence: str = "high", flags: list[str] | None = None) -> dict:
    return {
        "score": {
            "product_fit": total * 0.3,
            "team_execution": total * 0.25,
            "market_timing": total * 0.2,
            "traction": total * 0.15,
            "differentiation": total * 0.1,
            "total": total,
        },
        "confidence": confidence,
        "flags": flags or [],
    }


def test_determine_call_high_confidence_uses_raw_score_mapping():
    call, note = determine_call(_analysis(75))

    assert call == "Meeting"
    assert "75" in note


def test_determine_call_low_confidence_defaults_to_watch_from_pass():
    call, note = determine_call(_analysis(20, confidence="low", flags=["missing_founders"]))

    assert call == "Watch"
    assert "missing_founders" in note


def test_determine_call_low_confidence_defaults_to_watch_from_meeting():
    call, note = determine_call(_analysis(85, confidence="low", flags=["thin_source_data"]))

    assert call == "Watch"
    assert "Meeting" in note  # notes what the raw score would otherwise have mapped to


def test_top_falsifiers_picks_largest_gaps():
    analysis = {
        "score": {
            "product_fit": 30,  # maxed, gap 0
            "team_execution": 0,  # gap 25 (largest)
            "market_timing": 5,  # gap 15
            "traction": 15,  # maxed, gap 0
            "differentiation": 0,  # gap 10
            "total": 50,
        }
    }

    falsifiers = top_falsifiers(analysis, n=3)

    assert len(falsifiers) == 3
    # team_execution's gap (25) is the largest, so its falsifier must be first.
    from recommendation.generate import FALSIFIER_TEMPLATES

    assert falsifiers[0] == FALSIFIER_TEMPLATES["team_execution"]
