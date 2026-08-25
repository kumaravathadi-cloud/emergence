# Implementation Plan

Ordered build steps against the structure in [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md).
Each step produces something runnable/testable before the next starts.

## 0. Scaffolding
- `pyproject.toml`, package skeletons for `sourcing/`, `analysis/`, `recommendation/`,
  `common/`, `orchestrator/`, each with `__init__.py` and `tests/`.
- `common/retry.py` — retry-with-backoff wrapper, generic, no business logic.
- `common/logging.py` — structured per-run logger, writes `logs/<run_id>.log`.
- `schemas/candidate.v1.json`, `schemas/analysis.v1.json` — JSON Schema definitions
  matching the fields already listed in [VISION.md](VISION.md) §5 and [thesis.md](../thesis.md).

## 1. Sourcing system
- `sourcing/fetch.py` — Hacker News client (Algolia API, no auth) and YC company
  directory client (scraping ycombinator.com/companies, no auth/registration needed).
- `sourcing/normalize.py` — raw source payloads → candidate schema (name, site,
  one-liner, founders, signal, source_url).
- `sourcing/main.py` — `sourcing run --topic "..."`, wraps fetch+normalize in
  `common/retry.py`, writes `data/raw/<run_id>/candidates.json` validated against
  `schemas/candidate.v1.json`.
- Tests: normalization logic against fixture payloads from both sources; a
  thin/missing-field candidate produces a flagged low-data record, not an error.
- **Checkpoint:** run against a real topic, commit a sample `candidates.json`.

## 2. Analysis system
- `analysis/prompts.py` — structured-extract + scoring prompt, reads `thesis.md`
  directly (single source of truth, not copied into the prompt file).
- `analysis/score.py` — applies the thesis rubric weights to the LLM's structured
  output, produces the 0–100 score.
- `analysis/main.py` — `analysis run --input candidates.json`, validates each LLM
  response against `schemas/analysis.v1.json`, one retry on validation failure, then
  degrades to low-confidence per [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) Reliability.
- Tests: scoring math against known rubric inputs; schema-validation retry/degrade
  path with a deliberately malformed LLM response fixture.
- **Checkpoint:** run against the sample `candidates.json`, commit a sample
  `analysis/<company>.json`.
- **Blocked on:** LLM `base_url` / model name / API key.

## 3. Recommendation system
- `recommendation/template.py` — memo template: call, rationale, 2–3 falsifiers,
  cited sources.
- `recommendation/generate.py` — fills the template from analysis JSON, applies the
  thesis's score-to-call mapping, honors the low-confidence flag (nudges toward Watch).
- `recommendation/main.py` — `recommendation run --input analysis/*.json`, writes
  `memos/<run_id>/<company>.md`.
- Tests: call mapping at rubric boundaries (39/40, 69/70); low-confidence flag changes
  the call as expected.
- **Checkpoint:** commit a sample memo, confirm it's readable in <60s cold.

## 4. Orchestrator
- `orchestrator/run.py` — single command chaining the three `main.py` entrypoints by
  `run_id`, no logic of its own beyond wiring.
- **Checkpoint:** one command, topic in, memos out, end to end.

## 5. Full run
- Run against the real thesis topic, commit the full `data/`, `memos/`, `logs/` output.
- `README.md` — how to run, how to read outputs, env vars needed.

## Open blockers
| Step | Blocked on |
|---|---|
| Analysis | LLM `base_url`, model name, API key |