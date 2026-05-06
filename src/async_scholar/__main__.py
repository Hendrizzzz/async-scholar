from __future__ import annotations

import argparse
import sys
from pathlib import Path

from async_scholar import __version__
from async_scholar.demo import run_fixture_demo


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="async_scholar",
        description=(
            "AsyncScholar is a local-first lecture monitoring scaffold for "
            "transcription, event detection, alerts, archives, and review."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command")
    fixture_demo = subparsers.add_parser(
        "fixture-demo",
        help="run a transcript fixture through event detection and file artifacts",
    )
    fixture_demo.add_argument(
        "fixture_path",
        type=Path,
        help="path to a transcript JSONL fixture",
    )
    fixture_demo.add_argument(
        "--output-root",
        type=Path,
        default=Path("data") / "sessions",
        help="root directory for generated session artifacts",
    )
    fixture_demo.set_defaults(handler=_run_fixture_demo_command)

    subparsers.add_parser(
        "mic-recording-diagnostic",
        help="run the bounded microphone recording diagnostic",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv[:1] == ["mic-recording-diagnostic"]:
        return _run_mic_recording_diagnostic_command(argv[1:])

    parser = build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        return 0
    return handler(args)


def _run_fixture_demo_command(args: argparse.Namespace) -> int:
    result = run_fixture_demo(
        args.fixture_path,
        output_root=args.output_root,
    )
    paths = result.artifact_paths

    print("Fixture demo complete.")
    print(f"Session: {result.session_id}")
    print(f"Segments loaded: {result.segment_count}")
    print(f"Events detected: {result.event_count}")
    print(f"Output directory: {paths.output_dir}")
    print(f"Events JSONL: {paths.events_path}")
    print(f"Fake alert log: {paths.alerts_path}")
    print(f"Reviewer: {paths.reviewer_path}")
    return 0


def _run_mic_recording_diagnostic_command(argv: list[str]) -> int:
    from async_scholar.audio.mic_recording_diagnostic import (
        main as run_mic_recording_diagnostic,
    )

    return run_mic_recording_diagnostic(argv)


if __name__ == "__main__":
    raise SystemExit(main())
