#!/usr/bin/env python3
"""Run the automated test suite while collecting line coverage information."""

from __future__ import annotations

import argparse
import io
import sys
import trace
from contextlib import redirect_stdout
from pathlib import Path

import pytest


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="Additional arguments to forward to pytest",
    )
    parser.add_argument(
        "--output-dir",
        default="coverage_report",
        help="Directory where coverage artefacts should be written",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_argument_parser()
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parent.parent
    report_dir = repo_root / args.output_dir
    report_dir.mkdir(parents=True, exist_ok=True)

    tracer = trace.Trace(count=True, trace=False, ignoredirs=[sys.prefix, sys.exec_prefix])

    exit_code = tracer.runfunc(pytest.main, args.pytest_args or ["tests"])

    results = tracer.results()
    summary_buffer = io.StringIO()
    raw_dir = report_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    with redirect_stdout(summary_buffer):
        results.write_results(show_missing=True, summary=True, coverdir=str(raw_dir))

    summary_text = summary_buffer.getvalue()
    (report_dir / "coverage.txt").write_text(summary_text, encoding="utf-8")
    print(summary_text)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
