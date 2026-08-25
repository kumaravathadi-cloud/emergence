"""CLI: `recommendation run --input data/analysis/<run_id>` -> writes memos/<run_id>/<company>.md.

Accepts either a directory of analysis JSON files or an explicit glob pattern,
matching the `recommendation run --input analysis/*.json` shape from
IMPLEMENTATION_PLAN.md.
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

from common.logging import get_run_logger, log_event
from recommendation.generate import determine_call, top_falsifiers
from recommendation.template import render_memo

MEMOS_DIR = Path("memos")


def _resolve_input_files(input_arg: str) -> list[Path]:
    path = Path(input_arg)
    if path.is_dir():
        return sorted(path.glob("*.json"))
    return sorted(Path(p) for p in glob.glob(input_arg))


def run(input_arg: str) -> Path:
    files = _resolve_input_files(input_arg)
    if not files:
        raise FileNotFoundError(f"no analysis files matched: {input_arg}")

    analyses = [json.loads(f.read_text()) for f in files]
    run_id = analyses[0]["run_id"]
    logger = get_run_logger(run_id)

    out_dir = MEMOS_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    for path, analysis in zip(files, analyses, strict=True):
        call, note = determine_call(analysis)
        falsifiers = top_falsifiers(analysis)
        memo = render_memo(analysis, call=call, call_note=note, falsifiers=falsifiers)
        (out_dir / f"{path.stem}.md").write_text(memo)
        log_event(
            logger,
            stage="recommendation",
            candidate=analysis["candidate_name"],
            status="ok",
            call=call,
        )

    return out_dir


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="recommendation")
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="Generate memos from an analysis run.")
    run_parser.add_argument(
        "--input", required=True, help="A directory or glob of analysis/*.json files."
    )

    args = parser.parse_args(argv)
    if args.command == "run":
        out_dir = run(args.input)
        print(out_dir)


if __name__ == "__main__":
    main()
