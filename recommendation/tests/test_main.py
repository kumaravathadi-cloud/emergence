import pytest

from recommendation.main import run


def test_run_on_empty_analysis_dir_completes_without_error(tmp_path, monkeypatch):
    """A topic that legitimately sourced zero candidates leaves an empty
    data/analysis/<run_id>/ dir — recommendation should finish with zero memos,
    not crash, since this is a valid outcome rather than a bad --input path."""
    monkeypatch.chdir(tmp_path)
    run_id = "20260101-000000-abcdef"
    analysis_dir = tmp_path / "data" / "analysis" / run_id
    analysis_dir.mkdir(parents=True)

    out_dir = run(str(analysis_dir))

    assert out_dir.name == run_id
    assert out_dir.exists()
    assert list(out_dir.glob("*.md")) == []


def test_run_on_missing_path_raises():
    with pytest.raises(FileNotFoundError):
        run("data/analysis/does-not-exist-*.json")
