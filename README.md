# Emergence — AI-Augmented Investment Pipeline

Topic in, ranked/sourced VC memos out. One command runs three independently
re-runnable stages — sourcing → analysis → recommendation — file-handed-off
through `data/` and `memos/`, scored against the fixed thesis in
[thesis.md](thesis.md). See [docs/VISION.md](docs/VISION.md) and
[docs/SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md) for the full design, and
[docs/PROCESS.md](docs/PROCESS.md) for how the build was approached.

## Setup

```bash
uv sync
cp .env.example .env   # fill in the OPENAI_* values (see Environment variables below)
```

## Running

The whole pipeline, one command:

```bash
uv run python -m orchestrator.run run --topic "invoice reconciliation"
```

This generates one `run_id` and chains all three stages under it. Each stage
is also independently runnable and re-runnable by `run_id`, since the
`data/` files *are* the interface between stages:

```bash
uv run python -m sourcing.main run --topic "invoice reconciliation" [--run-id ID] [--hits-per-page 20]
uv run python -m analysis.main run --input data/raw/<run_id>/candidates.json
uv run python -m recommendation.main run --input data/analysis/<run_id>
```

Re-running just `analysis` or `recommendation` on an existing `run_id` reuses
the previously sourced/analyzed data — no network calls needed to redo the
downstream stages.

## Reading outputs

For a given `<run_id>`:

| Path | What it is |
|---|---|
| `data/raw/<run_id>/candidates.json` | Sourced candidates (YC directory + Hacker News), normalized, `low_data`-flagged where thin |
| `data/analysis/<run_id>/<company>.json` | Thesis-scored, every claim cited; `confidence: low` where source data was thin |
| `memos/<run_id>/<company>.md` | The memo — skim the **Call** line, then Rationale, then "What would change this call" |
| `logs/<run_id>.log` | One structured JSON line per candidate per stage — traces what happened to any candidate across the whole run without re-running anything |

A memo's call is one of **Pass / Watch / Meeting** per `thesis.md`'s score
mapping; a low-confidence analysis always defaults to **Watch** regardless of
its raw score, since thin source data doesn't warrant a firm Pass or Meeting.

A full sample run (`run_id 20260825-142916-0d7264`, topic "AI agent for
bookkeeping") is committed under `data/`, `memos/`, and `logs/` — read it
directly if you want to see real output without running anything.

## Environment variables

`.env.example` documents all of these; only the `OPENAI_*` block is a secret
you need to supply — the sourcing values are public, non-secret endpoint
config, kept in `.env` so they can be changed without a code edit.

| Variable | Used by | Notes |
|---|---|---|
| `OPENAI_API_KEY`, `OPENAI_ENDPOINT`, `OPENAI_API_VERSION`, `OPENAI_MODEL` | `analysis` | Azure OpenAI (or an Azure-API-compatible gateway) |
| `YC_ALGOLIA_APP_ID`, `YC_ALGOLIA_API_KEY`, `YC_ALGOLIA_INDEX`, `YC_COMPANY_URL_TEMPLATE` | `sourcing` | The same public, search-only key `ycombinator.com/companies` embeds client-side; not a secret |
| `HN_ALGOLIA_SEARCH_URL` | `sourcing` | Public HN Algolia Search API, no auth |
| `SOURCING_USER_AGENT`, `SOURCING_HTTP_TIMEOUT_SECONDS` | `sourcing` | Outbound HTTP identity/timeout for the YC and HN clients |

## Testing

```bash
uv run pytest        # unit tests, no live network calls — external sources are mocked
uv run ruff check .
uv run ruff format .
```

## Notes on sourcing

Product Hunt was the original second source (see `docs/VISION.md`'s history),
but its search and product pages sit behind a Cloudflare bot challenge with no
scrapable surface, so sourcing uses the **YC company directory** instead —
queried via the same public, read-only Algolia key YC's own site uses, with
founder names read from the JSON YC's company pages server-render into the
page HTML (no JS execution needed).
