from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from async_scholar import __version__
from async_scholar.demo import run_fixture_demo

_CRASH_RECOVERY_PREFLIGHT_CLI_ERROR = (
    "crash recovery session preflight could not be built"
)


class _FixedMessageArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.exit(2, f"{_CRASH_RECOVERY_PREFLIGHT_CLI_ERROR}\n")


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

    recovery_preflight = subparsers.add_parser(
        "crash-recovery-preflight",
        help="summarize read-only crash-recovery metadata for a session",
        description=(
            "Summarize read-only crash-recovery metadata for one explicit session root."
        ),
    )
    _add_crash_recovery_preflight_arguments(recovery_preflight)
    recovery_preflight.set_defaults(handler=_run_crash_recovery_preflight_command)

    subparsers.add_parser(
        "mic-recording-diagnostic",
        help="run the bounded microphone recording diagnostic",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv[:1] == ["mic-recording-diagnostic"]:
        return _run_mic_recording_diagnostic_command(argv[1:])
    if argv[:1] == ["crash-recovery-preflight"]:
        return _run_crash_recovery_preflight_argv(argv[1:])
    if "crash-recovery-preflight" in argv or any(
        arg == "--sessions-root" or arg.startswith("--sessions-root=") for arg in argv
    ):
        print(_CRASH_RECOVERY_PREFLIGHT_CLI_ERROR, file=sys.stderr)
        return 2

    parser = build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        return 0
    return handler(args)


def _add_crash_recovery_preflight_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe session identifier to inspect",
    )
    parser.add_argument(
        "--sessions-root",
        type=Path,
        required=True,
        help="explicit root directory containing session artifact directories",
    )


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


def _run_crash_recovery_preflight_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar crash-recovery-preflight",
        description=(
            "Summarize read-only crash-recovery metadata for one explicit session root."
        ),
    )
    _add_crash_recovery_preflight_arguments(parser)
    args = parser.parse_args(argv)
    return _run_crash_recovery_preflight_command(args)


def _run_crash_recovery_preflight_command(args: argparse.Namespace) -> int:
    from async_scholar.session_recovery import (
        CRASH_RECOVERY_PREFLIGHT_ERROR,
        build_crash_recovery_session_preflight,
        crash_recovery_session_preflight_safe_summary,
    )

    try:
        preflight = build_crash_recovery_session_preflight(
            args.sessions_root,
            args.session_id,
        )
        payload = crash_recovery_session_preflight_safe_summary(preflight)
    except ValueError:
        print(CRASH_RECOVERY_PREFLIGHT_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _run_mic_recording_diagnostic_command(argv: list[str]) -> int:
    from async_scholar.audio.mic_recording_diagnostic import (
        main as run_mic_recording_diagnostic,
    )

    return run_mic_recording_diagnostic(argv)


if __name__ == "__main__":
    raise SystemExit(main())
