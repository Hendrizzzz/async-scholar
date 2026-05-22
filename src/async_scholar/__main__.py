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
_ARCHIVE_EXPORT_PREFLIGHT_CLI_ERROR = "archive export preflight could not be built"
_ARCHIVE_EXPORT_CLI_ERROR = "archive export could not be executed"
_ARCHIVE_EXPORT_VERIFY_CLI_ERROR = "archive export verification could not be built"
_ARCHIVE_DELETE_DRY_RUN_CLI_ERROR = "archive delete dry run could not be built"
_SCHEDULED_START_PREVIEW_CLI_ERROR = "scheduled start preview could not be built"


class _FixedMessageArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args: object, fixed_error_message: str, **kwargs: object):
        super().__init__(*args, **kwargs)
        self._fixed_error_message = fixed_error_message

    def error(self, message: str) -> None:
        self.exit(2, f"{self._fixed_error_message}\n")


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

    archive_export_preflight = subparsers.add_parser(
        "archive-export-preflight",
        help="summarize read-only archive export metadata for a session",
        description=(
            "Summarize read-only archive export metadata for one explicit "
            "session archive root."
        ),
    )
    _add_archive_export_preflight_arguments(archive_export_preflight)
    archive_export_preflight.set_defaults(handler=_run_archive_export_preflight_command)

    archive_export_local = subparsers.add_parser(
        "archive-export-local",
        help="copy allowlisted archive artifacts to an explicit local export root",
        description=(
            "Copy allowlisted archive artifacts for one explicit local session "
            "archive root to one explicit existing local export root."
        ),
    )
    _add_archive_export_local_arguments(archive_export_local)
    archive_export_local.set_defaults(handler=_run_archive_export_local_command)

    archive_export_verify = subparsers.add_parser(
        "archive-export-verify-local",
        help="verify a local archive export using metadata only",
        description=(
            "Verify allowlisted archive export metadata for one explicit local "
            "session archive root and one explicit existing local export root."
        ),
    )
    _add_archive_export_verify_local_arguments(archive_export_verify)
    archive_export_verify.set_defaults(handler=_run_archive_export_verify_local_command)

    archive_delete_dry_run = subparsers.add_parser(
        "archive-delete-dry-run-local",
        help="summarize a local archive delete dry run using metadata only",
        description=(
            "Summarize a read-only local archive delete dry run for one "
            "explicit session archive root."
        ),
    )
    _add_archive_delete_dry_run_local_arguments(archive_delete_dry_run)
    archive_delete_dry_run.set_defaults(
        handler=_run_archive_delete_dry_run_local_command
    )

    scheduled_start_preview = subparsers.add_parser(
        "scheduled-start-preview-local",
        help="preview scheduled-start metadata without executing",
        description=(
            "Preview one non-executing scheduled-start decision from explicit "
            "local metadata and an explicit local clock."
        ),
    )
    _add_scheduled_start_preview_local_arguments(scheduled_start_preview)
    scheduled_start_preview.set_defaults(
        handler=_run_scheduled_start_preview_local_command
    )

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
    if argv[:1] == ["archive-delete-dry-run-local"]:
        return _run_archive_delete_dry_run_local_argv(argv[1:])
    if "archive-delete-dry-run-local" in argv:
        print(_ARCHIVE_DELETE_DRY_RUN_CLI_ERROR, file=sys.stderr)
        return 2
    if argv[:1] == ["scheduled-start-preview-local"]:
        return _run_scheduled_start_preview_local_argv(argv[1:])
    if "scheduled-start-preview-local" in argv or any(
        arg == "--course-id"
        or arg.startswith("--course-id=")
        or arg == "--day-of-week"
        or arg.startswith("--day-of-week=")
        or arg == "--local-start-time"
        or arg.startswith("--local-start-time=")
        or arg == "--duration-minutes"
        or arg.startswith("--duration-minutes=")
        or arg == "--source-kind"
        or arg.startswith("--source-kind=")
        or arg == "--clock-day-of-week"
        or arg.startswith("--clock-day-of-week=")
        or arg == "--clock-local-time"
        or arg.startswith("--clock-local-time=")
        or arg == "--disabled"
        for arg in argv
    ):
        print(_SCHEDULED_START_PREVIEW_CLI_ERROR, file=sys.stderr)
        return 2
    if argv[:1] == ["archive-export-preflight"]:
        return _run_archive_export_preflight_argv(argv[1:])
    if argv[:1] == ["archive-export-verify-local"]:
        return _run_archive_export_verify_local_argv(argv[1:])
    if "archive-export-verify-local" in argv:
        print(_ARCHIVE_EXPORT_VERIFY_CLI_ERROR, file=sys.stderr)
        return 2
    if argv[:1] == ["archive-export-local"]:
        return _run_archive_export_local_argv(argv[1:])
    if "archive-export-local" in argv or any(
        arg == "--export-root" or arg.startswith("--export-root=") for arg in argv
    ):
        print(_ARCHIVE_EXPORT_CLI_ERROR, file=sys.stderr)
        return 2
    if "archive-export-preflight" in argv or any(
        arg == "--archive-root" or arg.startswith("--archive-root=") for arg in argv
    ):
        print(_ARCHIVE_EXPORT_PREFLIGHT_CLI_ERROR, file=sys.stderr)
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


def _add_archive_export_preflight_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe session identifier to inspect",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit root directory containing session archive directories",
    )


def _add_archive_export_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe session identifier to export",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit root directory containing session archive directories",
    )
    parser.add_argument(
        "--export-root",
        type=Path,
        required=True,
        help="explicit existing local root directory for copied export artifacts",
    )


def _add_archive_export_verify_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe session identifier to verify",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit root directory containing session archive directories",
    )
    parser.add_argument(
        "--export-root",
        type=Path,
        required=True,
        help="explicit existing local root directory containing exported artifacts",
    )


def _add_archive_delete_dry_run_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe session identifier to inspect",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit root directory containing session archive directories",
    )


def _add_scheduled_start_preview_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe local session identifier to preview",
    )
    parser.add_argument(
        "--course-id",
        required=True,
        help="safe course identifier for the preview",
    )
    parser.add_argument(
        "--day-of-week",
        required=True,
        help="scheduled weekday name",
    )
    parser.add_argument(
        "--local-start-time",
        required=True,
        help="scheduled local start time in HH:MM",
    )
    parser.add_argument(
        "--duration-minutes",
        required=True,
        type=int,
        help="scheduled class duration in minutes",
    )
    parser.add_argument(
        "--source-kind",
        required=True,
        choices=("file", "mic"),
        help="local source kind to preview",
    )
    parser.add_argument(
        "--clock-day-of-week",
        required=True,
        help="explicit local clock weekday name",
    )
    parser.add_argument(
        "--clock-local-time",
        required=True,
        help="explicit local clock time in HH:MM",
    )
    parser.add_argument(
        "--disabled",
        action="store_true",
        help="preview the schedule as disabled",
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
        fixed_error_message=_CRASH_RECOVERY_PREFLIGHT_CLI_ERROR,
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


def _run_archive_export_preflight_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar archive-export-preflight",
        description=(
            "Summarize read-only archive export metadata for one explicit "
            "session archive root."
        ),
        fixed_error_message=_ARCHIVE_EXPORT_PREFLIGHT_CLI_ERROR,
    )
    _add_archive_export_preflight_arguments(parser)
    args = parser.parse_args(argv)
    return _run_archive_export_preflight_command(args)


def _run_archive_export_preflight_command(args: argparse.Namespace) -> int:
    from async_scholar.archive_export import (
        archive_export_preflight_summary_safe_summary,
        build_archive_export_preflight_summary_from_root,
    )

    try:
        preflight = build_archive_export_preflight_summary_from_root(
            args.archive_root,
            args.session_id,
        )
        payload = archive_export_preflight_summary_safe_summary(preflight)
    except ValueError:
        print(_ARCHIVE_EXPORT_PREFLIGHT_CLI_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _run_archive_export_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar archive-export-local",
        description=(
            "Copy allowlisted archive artifacts for one explicit local session "
            "archive root to one explicit existing local export root."
        ),
        fixed_error_message=_ARCHIVE_EXPORT_CLI_ERROR,
    )
    _add_archive_export_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_archive_export_local_command(args)


def _run_archive_export_local_command(args: argparse.Namespace) -> int:
    from async_scholar.archive_export import (
        archive_export_execution_result_safe_summary,
        execute_archive_export_to_local_root,
    )

    try:
        export_result = execute_archive_export_to_local_root(
            args.archive_root,
            args.export_root,
            args.session_id,
        )
        payload = archive_export_execution_result_safe_summary(export_result)
    except ValueError:
        print(_ARCHIVE_EXPORT_CLI_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _run_archive_export_verify_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar archive-export-verify-local",
        description=(
            "Verify allowlisted archive export metadata for one explicit local "
            "session archive root and one explicit existing local export root."
        ),
        fixed_error_message=_ARCHIVE_EXPORT_VERIFY_CLI_ERROR,
    )
    _add_archive_export_verify_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_archive_export_verify_local_command(args)


def _run_archive_export_verify_local_command(args: argparse.Namespace) -> int:
    from async_scholar.archive_export import (
        archive_export_verification_summary_safe_summary,
        build_archive_export_verification_summary_from_roots,
    )

    try:
        verification = build_archive_export_verification_summary_from_roots(
            args.archive_root,
            args.export_root,
            args.session_id,
        )
        payload = archive_export_verification_summary_safe_summary(verification)
    except ValueError:
        print(_ARCHIVE_EXPORT_VERIFY_CLI_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _run_archive_delete_dry_run_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar archive-delete-dry-run-local",
        description=(
            "Summarize a read-only local archive delete dry run for one "
            "explicit session archive root."
        ),
        fixed_error_message=_ARCHIVE_DELETE_DRY_RUN_CLI_ERROR,
    )
    _add_archive_delete_dry_run_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_archive_delete_dry_run_local_command(args)


def _run_archive_delete_dry_run_local_command(args: argparse.Namespace) -> int:
    from async_scholar.archive_delete_dry_run_result import (
        ARCHIVE_DELETE_DRY_RUN_LOCAL_ERROR,
        build_archive_delete_dry_run_local_result,
        export_archive_delete_dry_run_local_result,
    )

    try:
        dry_run = build_archive_delete_dry_run_local_result(
            args.archive_root,
            args.session_id,
        )
        payload = export_archive_delete_dry_run_local_result(dry_run)
    except ValueError:
        print(ARCHIVE_DELETE_DRY_RUN_LOCAL_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _run_scheduled_start_preview_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar scheduled-start-preview-local",
        description=(
            "Preview one non-executing scheduled-start decision from explicit "
            "local metadata and an explicit local clock."
        ),
        fixed_error_message=_SCHEDULED_START_PREVIEW_CLI_ERROR,
    )
    _add_scheduled_start_preview_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_scheduled_start_preview_local_command(args)


def _run_scheduled_start_preview_local_command(args: argparse.Namespace) -> int:
    from async_scholar.schedule_config import ScheduleConfig
    from async_scholar.scheduled_start import (
        ScheduledStartClock,
        build_scheduled_start_manual_result,
        build_scheduled_start_plan,
        scheduled_start_manual_result_safe_summary,
    )

    try:
        schedule_config = ScheduleConfig(
            course_id=args.course_id,
            class_times=[
                {
                    "day_of_week": args.day_of_week,
                    "local_start_time": args.local_start_time,
                    "duration_minutes": args.duration_minutes,
                }
            ],
        )
        plan = build_scheduled_start_plan(
            schedule_config,
            selected_class_time_index=0,
            source_kind=args.source_kind,
            enabled=not args.disabled,
        )
        clock = ScheduledStartClock(
            day_of_week=args.clock_day_of_week,
            local_time=args.clock_local_time,
        )
        preview = build_scheduled_start_manual_result(
            plan,
            clock,
            args.session_id,
        )
        payload = scheduled_start_manual_result_safe_summary(preview)
    except ValueError:
        print(_SCHEDULED_START_PREVIEW_CLI_ERROR, file=sys.stderr)
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
