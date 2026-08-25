"""CLI: `orchestrator run --topic "..."` -> chains sourcing -> analysis -> recommendation.

No business logic of its own: generates (or reuses) one run_id and hands it
through the three stage entrypoints, each of which reads/writes only the
files at their documented SYSTEM_DESIGN.md stage boundary.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from analysis.main import run as analysis_run
from recommendation.main import run as recommendation_run
from sourcing.main import new_run_id
from sourcing.main import run as sourcing_run


def run(topic: str, *, run_id: str | None = None, hits_per_page: int = 20) -> dict[str, str | Path]:
    run_id = run_id or new_run_id()

    candidates_path = sourcing_run(topic, run_id=run_id, hits_per_page=hits_per_page)
    analysis_dir = analysis_run(candidates_path)
    memos_dir = recommendation_run(analysis_dir)

    return {
        "run_id": run_id,
        "candidates": candidates_path,
        "analysis": analysis_dir,
        "memos": memos_dir,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="Source, analyze, and recommend for one topic.")
    run_parser.add_argument("--topic", required=True)
    run_parser.add_argument(
        "--run-id", default=None, help="Reuse an existing run_id instead of generating one."
    )
    run_parser.add_argument("--hits-per-page", type=int, default=20)

    args = parser.parse_args(argv)
    if args.command == "run":
        result = run(args.topic, run_id=args.run_id, hits_per_page=args.hits_per_page)
        print(f"run_id:     {result['run_id']}")
        print(f"candidates: {result['candidates']}")
        print(f"analysis:   {result['analysis']}")
        print(f"memos:      {result['memos']}")


if __name__ == "__main__":
    main()
