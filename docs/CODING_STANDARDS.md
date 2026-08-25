# Coding Standards

## Environment
- Python, managed with `uv` — `uv venv`, `uv sync`, `uv run <cmd>`.
- Dependencies pinned in `pyproject.toml` / `uv.lock`, committed.

## Style
- Type hints on every function signature.
- Formatting + linting via `ruff` (`uv run ruff format`, `uv run ruff check`).
- One module = one responsibility, matching the package boundaries in
  [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) (`fetch.py`, `normalize.py`, `score.py`, etc.).

## Testing
- `pytest`, run via `uv run pytest`.
- Each system (`sourcing/`, `analysis/`, `recommendation/`) owns its `tests/`.
- Test what's risky, not everything:
  - **Sourcing** — normalization from raw payload to candidate schema; thin/missing
    fields degrade to a flagged record.
  - **Analysis** — scoring math against the rubric; schema-validation retry/degrade
    path on a malformed LLM response.
  - **Recommendation** — score-to-call mapping at its boundaries; low-confidence flag
    changes the call correctly.
- External calls (PH scrape, HN API, LLM) are mocked in tests via fixture payloads —
  no live network calls in the test suite.
- No coverage target; a module gets a test because its failure mode is real, not to
  hit a number.