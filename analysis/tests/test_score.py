import pytest

from analysis.score import RUBRIC_WEIGHTS, compute_score


def test_compute_score_full_fit_gives_max_points():
    result = compute_score(dict.fromkeys(RUBRIC_WEIGHTS, 1.0))

    assert result["total"] == 100
    for category, weight in RUBRIC_WEIGHTS.items():
        assert result[category] == weight


def test_compute_score_zero_fit_gives_zero():
    result = compute_score(dict.fromkeys(RUBRIC_WEIGHTS, 0.0))

    assert result["total"] == 0


def test_compute_score_partial_fit():
    result = compute_score(dict.fromkeys(RUBRIC_WEIGHTS, 0.5))

    assert result["total"] == 50


@pytest.mark.parametrize("value,expected_total", [(1.5, 100.0), (-0.5, 0.0)])
def test_compute_score_clamps_out_of_range_fit(value, expected_total):
    result = compute_score(dict.fromkeys(RUBRIC_WEIGHTS, value))

    assert result["total"] == pytest.approx(expected_total)


def test_compute_score_missing_category_raises():
    fit = dict.fromkeys(RUBRIC_WEIGHTS, 0.5)
    del fit["traction"]

    with pytest.raises(ValueError):
        compute_score(fit)
