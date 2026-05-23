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
_COURSE_SCHEDULE_SAVE_CLI_ERROR = "course schedule save could not be built"
_COURSE_SCHEDULE_SUMMARY_CLI_ERROR = "course schedule summary could not be built"
_COURSE_SCHEDULE_LIST_CLI_ERROR = "course schedule list could not be built"
_SCHEDULED_START_PREVIEW_FROM_STORE_CLI_ERROR = (
    "stored scheduled start preview could not be built"
)
_SCHEDULED_START_NEXT_FROM_STORE_CLI_ERROR = (
    "stored next scheduled start preview could not be built"
)
_SCHEDULED_START_DUE_LIST_FROM_STORE_CLI_ERROR = (
    "stored scheduled start due list could not be built"
)
_SESSION_STOP_PREVIEW_FROM_STORE_CLI_ERROR = (
    "stored session stop preview could not be built"
)
_SESSION_WINDOW_PLAN_FROM_STORE_CLI_ERROR = (
    "stored session window plan could not be built"
)
_SESSION_WINDOW_ARCHIVE_PREFLIGHT_FROM_STORE_CLI_ERROR = (
    "stored session window archive preflight could not be built"
)
_SESSION_WINDOW_ALERT_PREVIEW_FROM_STORE_CLI_ERROR = (
    "stored session window alert preview could not be built"
)
_SESSION_WINDOW_READINESS_PREFLIGHT_FROM_STORE_CLI_ERROR = (
    "stored session window readiness preflight could not be built"
)
_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_FROM_STORE_CLI_ERROR = (
    "stored session window confirmation preflight could not be built"
)
_SESSION_WINDOW_CONFIRMATION_RESPONSE_FROM_STORE_CLI_ERROR = (
    "stored session window confirmation response could not be built"
)
_COURSE_SCHEDULE_SAFE_SUMMARY_KEYS = ("course_id", "class_time_count")
_STORED_SCHEDULED_START_PREVIEW_KEYS = (
    "status",
    "session_id",
    "course_id",
    "source_kind",
    "clock_day_of_week",
    "clock_local_time",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "due",
    "minutes_until_start",
    "next_day_of_week",
    "next_local_start_time",
)
_STORED_SCHEDULED_START_NEXT_PREVIEW_KEYS = (
    "status",
    "session_id",
    "course_id",
    "source_kind",
    "clock_day_of_week",
    "clock_local_time",
    "selected_class_time_index",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "due",
    "minutes_until_start",
    "next_day_of_week",
    "next_local_start_time",
)
_STORED_SCHEDULED_START_DUE_LIST_KEYS = (
    "status",
    "session_id",
    "source_kind",
    "clock_day_of_week",
    "clock_local_time",
    "course_count",
    "due_count",
    "courses",
)
_STORED_SCHEDULED_START_DUE_LIST_COURSE_KEYS = (
    "course_id",
    "selected_class_time_index",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "due",
    "minutes_until_start",
)
_STORED_SESSION_STOP_PREVIEW_KEYS = (
    "status",
    "course_id",
    "source_kind",
    "selected_class_time_index",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "stop_after_minutes",
    "enabled",
)
_STORED_SESSION_WINDOW_PLAN_KEYS = (
    "status",
    "session_id",
    "source_kind",
    "clock_day_of_week",
    "clock_local_time",
    "course_count",
    "due_count",
    "courses",
)
_STORED_SESSION_WINDOW_PLAN_COURSE_KEYS = (
    "course_id",
    "selected_class_time_index",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "due",
    "minutes_until_start",
    "stop_after_minutes",
    "enabled",
)
_STORED_SESSION_WINDOW_ARCHIVE_PREFLIGHT_KEYS = (
    "status",
    "session_id",
    "source_kind",
    "clock_day_of_week",
    "clock_local_time",
    "course_count",
    "due_count",
    "archive_recovery_status",
    "archive_existing_count",
    "archive_missing_count",
    "archive_total_existing_size_bytes",
    "courses",
)
_STORED_SESSION_WINDOW_ARCHIVE_PREFLIGHT_COURSE_KEYS = (
    "course_id",
    "selected_class_time_index",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "due",
    "minutes_until_start",
    "stop_after_minutes",
    "enabled",
)
_STORED_SESSION_WINDOW_ALERT_PREVIEW_KEYS = (
    "status",
    "session_id",
    "source_kind",
    "clock_day_of_week",
    "clock_local_time",
    "course_count",
    "due_count",
    "alert_preview_count",
    "courses",
)
_STORED_SESSION_WINDOW_ALERT_PREVIEW_COURSE_KEYS = (
    "course_id",
    "selected_class_time_index",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "due",
    "minutes_until_start",
    "stop_after_minutes",
    "enabled",
    "alert_preview",
)
_STORED_SESSION_WINDOW_ALERT_PREVIEW_METADATA_KEYS = (
    "alert_kind",
    "delivery",
    "requires_confirmation",
)
_STORED_SESSION_WINDOW_ALERT_PREVIEW_METADATA = {
    "alert_kind": "participation_check",
    "delivery": "none",
    "requires_confirmation": True,
}
_STORED_SESSION_WINDOW_READINESS_PREFLIGHT_KEYS = (
    "status",
    "session_id",
    "source_kind",
    "clock_day_of_week",
    "clock_local_time",
    "course_count",
    "due_count",
    "alert_preview_count",
    "archive_recovery_status",
    "archive_existing_count",
    "archive_missing_count",
    "archive_total_existing_size_bytes",
    "ready_to_start",
    "courses",
)
_STORED_SESSION_WINDOW_READINESS_PREFLIGHT_COURSE_KEYS = (
    "course_id",
    "selected_class_time_index",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "due",
    "minutes_until_start",
    "stop_after_minutes",
    "enabled",
    "alert_preview",
)
_STORED_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_KEYS = (
    "status",
    "session_id",
    "source_kind",
    "clock_day_of_week",
    "clock_local_time",
    "course_count",
    "due_count",
    "ready_to_start",
    "confirmation_required",
    "confirmation_status",
    "blocked_execution_count",
    "courses",
)
_STORED_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_COURSE_KEYS = (
    "course_id",
    "selected_class_time_index",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "due",
    "minutes_until_start",
    "stop_after_minutes",
    "enabled",
    "requires_confirmation",
)
_STORED_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_STATUSES = frozenset(
    ("not_required", "required", "disabled")
)
_STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_KEYS = (
    "status",
    "session_id",
    "source_kind",
    "clock_day_of_week",
    "clock_local_time",
    "course_count",
    "due_count",
    "ready_to_start",
    "confirmation_required",
    "confirmation_status",
    "confirmation_response",
    "confirmation_verified",
    "confirmed_start_count",
    "blocked_execution_count",
    "courses",
)
_STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_COURSE_KEYS = (
    "course_id",
    "selected_class_time_index",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "due",
    "minutes_until_start",
    "stop_after_minutes",
    "enabled",
    "requires_confirmation",
    "confirmation_response",
)
_STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_STATUSES = frozenset(
    ("confirmed", "declined", "not_required", "disabled")
)
_STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_TOKENS = frozenset(
    ("confirmed", "declined")
)


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

    course_schedule_summary = subparsers.add_parser(
        "course-schedule-summary-local",
        help="summarize a stored local course schedule using metadata only",
        description=(
            "Summarize one stored local course schedule from an explicit "
            "read-only SQLite database path."
        ),
    )
    _add_course_schedule_summary_local_arguments(course_schedule_summary)
    course_schedule_summary.set_defaults(
        handler=_run_course_schedule_summary_local_command
    )

    course_schedule_list = subparsers.add_parser(
        "course-schedule-list-local",
        help="list stored local course schedules using metadata only",
        description=(
            "List stored local course schedule metadata from an explicit "
            "read-only SQLite database path."
        ),
    )
    _add_course_schedule_list_local_arguments(course_schedule_list)
    course_schedule_list.set_defaults(handler=_run_course_schedule_list_local_command)

    course_schedule_save = subparsers.add_parser(
        "course-schedule-save-local",
        help="save a local course schedule from explicit metadata",
        description=(
            "Save one validated local course schedule into an explicit SQLite "
            "database path without executing a scheduler."
        ),
    )
    _add_course_schedule_save_local_arguments(course_schedule_save)
    course_schedule_save.set_defaults(handler=_run_course_schedule_save_local_command)

    stored_schedule_preview = subparsers.add_parser(
        "scheduled-start-preview-from-store-local",
        help="preview stored scheduled-start metadata without executing",
        description=(
            "Preview one non-executing scheduled-start decision from an "
            "explicit read-only local schedule store and explicit local clock."
        ),
    )
    _add_scheduled_start_preview_from_store_local_arguments(stored_schedule_preview)
    stored_schedule_preview.set_defaults(
        handler=_run_scheduled_start_preview_from_store_local_command
    )

    stored_schedule_next_preview = subparsers.add_parser(
        "scheduled-start-next-from-store-local",
        help="preview the next stored scheduled-start metadata without executing",
        description=(
            "Preview the next non-executing scheduled-start decision from an "
            "explicit read-only local schedule store and explicit local clock."
        ),
    )
    _add_scheduled_start_next_from_store_local_arguments(stored_schedule_next_preview)
    stored_schedule_next_preview.set_defaults(
        handler=_run_scheduled_start_next_from_store_local_command
    )

    stored_schedule_due_list = subparsers.add_parser(
        "scheduled-start-due-list-from-store-local",
        help="list due stored scheduled-start metadata without executing",
        description=(
            "List due non-executing scheduled-start metadata from an explicit "
            "read-only local schedule store and explicit local clock."
        ),
    )
    _add_scheduled_start_due_list_from_store_local_arguments(stored_schedule_due_list)
    stored_schedule_due_list.set_defaults(
        handler=_run_scheduled_start_due_list_from_store_local_command
    )

    session_stop_preview = subparsers.add_parser(
        "session-stop-preview-from-store-local",
        help="preview stored session-stop metadata without executing",
        description=(
            "Preview one non-executing session-stop decision from an explicit "
            "read-only local schedule store."
        ),
    )
    _add_session_stop_preview_from_store_local_arguments(session_stop_preview)
    session_stop_preview.set_defaults(
        handler=_run_session_stop_preview_from_store_local_command
    )

    session_window_plan = subparsers.add_parser(
        "session-window-plan-from-store-local",
        help="plan due stored session windows without executing",
        description=(
            "Build due non-executing session-window metadata from an explicit "
            "read-only local schedule store and explicit local clock."
        ),
    )
    _add_session_window_plan_from_store_local_arguments(session_window_plan)
    session_window_plan.set_defaults(
        handler=_run_session_window_plan_from_store_local_command
    )

    session_window_archive_preflight = subparsers.add_parser(
        "session-window-archive-preflight-from-store-local",
        help="preflight due stored session windows against archive readiness",
        description=(
            "Build read-only session-window archive preflight metadata from an "
            "explicit read-only local schedule store, archive root, and local clock."
        ),
    )
    _add_session_window_archive_preflight_from_store_local_arguments(
        session_window_archive_preflight
    )
    session_window_archive_preflight.set_defaults(
        handler=_run_session_window_archive_preflight_from_store_local_command
    )

    session_window_alert_preview = subparsers.add_parser(
        "session-window-alert-preview-from-store-local",
        help="preview due stored session-window participation checks without delivery",
        description=(
            "Build metadata-only session-window alert preview data from an "
            "explicit read-only local schedule store and explicit local clock."
        ),
    )
    _add_session_window_alert_preview_from_store_local_arguments(
        session_window_alert_preview
    )
    session_window_alert_preview.set_defaults(
        handler=_run_session_window_alert_preview_from_store_local_command
    )

    session_window_readiness_preflight = subparsers.add_parser(
        "session-window-readiness-preflight-from-store-local",
        help="preflight due stored session windows for metadata-only readiness",
        description=(
            "Build read-only session-window readiness preflight metadata from an "
            "explicit read-only local schedule store, archive root, and local clock."
        ),
    )
    _add_session_window_readiness_preflight_from_store_local_arguments(
        session_window_readiness_preflight
    )
    session_window_readiness_preflight.set_defaults(
        handler=_run_session_window_readiness_preflight_from_store_local_command
    )

    session_window_confirmation_preflight = subparsers.add_parser(
        "session-window-confirmation-preflight-from-store-local",
        help="preflight due stored session windows for user confirmation",
        description=(
            "Build read-only session-window confirmation preflight metadata from an "
            "explicit read-only local schedule store, archive root, and local clock."
        ),
    )
    _add_session_window_confirmation_preflight_from_store_local_arguments(
        session_window_confirmation_preflight
    )
    session_window_confirmation_preflight.set_defaults(
        handler=_run_session_window_confirmation_preflight_from_store_local_command
    )

    session_window_confirmation_response = subparsers.add_parser(
        "session-window-confirmation-response-from-store-local",
        help="record a fixed user confirmation response for due stored session windows",
        description=(
            "Build non-executing session-window confirmation response metadata from "
            "an explicit read-only local schedule store, archive root, local clock, "
            "and fixed confirmation response."
        ),
    )
    _add_session_window_confirmation_response_from_store_local_arguments(
        session_window_confirmation_response
    )
    session_window_confirmation_response.set_defaults(
        handler=_run_session_window_confirmation_response_from_store_local_command
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
    if argv[:1] == ["scheduled-start-preview-from-store-local"]:
        return _run_scheduled_start_preview_from_store_local_argv(argv[1:])
    if argv[:1] == ["scheduled-start-next-from-store-local"]:
        return _run_scheduled_start_next_from_store_local_argv(argv[1:])
    if argv[:1] == ["scheduled-start-due-list-from-store-local"]:
        return _run_scheduled_start_due_list_from_store_local_argv(argv[1:])
    if argv[:1] == ["session-stop-preview-from-store-local"]:
        return _run_session_stop_preview_from_store_local_argv(argv[1:])
    if argv[:1] == ["session-window-plan-from-store-local"]:
        return _run_session_window_plan_from_store_local_argv(argv[1:])
    if argv[:1] == ["session-window-archive-preflight-from-store-local"]:
        return _run_session_window_archive_preflight_from_store_local_argv(argv[1:])
    if argv[:1] == ["session-window-alert-preview-from-store-local"]:
        return _run_session_window_alert_preview_from_store_local_argv(argv[1:])
    if argv[:1] == ["session-window-readiness-preflight-from-store-local"]:
        return _run_session_window_readiness_preflight_from_store_local_argv(argv[1:])
    if argv[:1] == ["session-window-confirmation-preflight-from-store-local"]:
        return _run_session_window_confirmation_preflight_from_store_local_argv(
            argv[1:]
        )
    if argv[:1] == ["session-window-confirmation-response-from-store-local"]:
        return _run_session_window_confirmation_response_from_store_local_argv(argv[1:])
    if argv[:1] == ["course-schedule-save-local"]:
        return _run_course_schedule_save_local_argv(argv[1:])
    if argv[:1] == ["course-schedule-summary-local"]:
        return _run_course_schedule_summary_local_argv(argv[1:])
    if argv[:1] == ["course-schedule-list-local"]:
        return _run_course_schedule_list_local_argv(argv[1:])
    if "course-schedule-list-local" in argv:
        print(_COURSE_SCHEDULE_LIST_CLI_ERROR, file=sys.stderr)
        return 2
    if "course-schedule-save-local" in argv or any(
        arg == "--class-time"
        or arg.startswith("--class-time=")
        or arg == "--title"
        or arg.startswith("--title=")
        or arg == "--instructor-name"
        or arg.startswith("--instructor-name=")
        or arg == "--meeting-url"
        or arg.startswith("--meeting-url=")
        or arg == "--meeting-label"
        or arg.startswith("--meeting-label=")
        for arg in argv
    ):
        print(_COURSE_SCHEDULE_SAVE_CLI_ERROR, file=sys.stderr)
        return 2
    if "scheduled-start-next-from-store-local" in argv:
        print(_SCHEDULED_START_NEXT_FROM_STORE_CLI_ERROR, file=sys.stderr)
        return 2
    if "scheduled-start-due-list-from-store-local" in argv:
        print(_SCHEDULED_START_DUE_LIST_FROM_STORE_CLI_ERROR, file=sys.stderr)
        return 2
    if "session-stop-preview-from-store-local" in argv:
        print(_SESSION_STOP_PREVIEW_FROM_STORE_CLI_ERROR, file=sys.stderr)
        return 2
    if "session-window-plan-from-store-local" in argv:
        print(_SESSION_WINDOW_PLAN_FROM_STORE_CLI_ERROR, file=sys.stderr)
        return 2
    if "session-window-archive-preflight-from-store-local" in argv:
        print(
            _SESSION_WINDOW_ARCHIVE_PREFLIGHT_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if "session-window-alert-preview-from-store-local" in argv:
        print(
            _SESSION_WINDOW_ALERT_PREVIEW_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if "session-window-readiness-preflight-from-store-local" in argv:
        print(
            _SESSION_WINDOW_READINESS_PREFLIGHT_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if "session-window-confirmation-preflight-from-store-local" in argv:
        print(
            _SESSION_WINDOW_CONFIRMATION_PREFLIGHT_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if "session-window-confirmation-response-from-store-local" in argv:
        print(
            _SESSION_WINDOW_CONFIRMATION_RESPONSE_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if any(
        arg == "--archive-root" or arg.startswith("--archive-root=") for arg in argv
    ) and any(arg == "--db-path" or arg.startswith("--db-path=") for arg in argv):
        print(
            _SESSION_WINDOW_ARCHIVE_PREFLIGHT_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if "scheduled-start-preview-from-store-local" in argv or any(
        arg == "--class-time-index" or arg.startswith("--class-time-index=")
        for arg in argv
    ):
        print(_SCHEDULED_START_PREVIEW_FROM_STORE_CLI_ERROR, file=sys.stderr)
        return 2
    if "course-schedule-summary-local" in argv or any(
        arg == "--db-path" or arg.startswith("--db-path=") for arg in argv
    ):
        print(_COURSE_SCHEDULE_SUMMARY_CLI_ERROR, file=sys.stderr)
        return 2
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


def _add_course_schedule_summary_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
    )
    parser.add_argument(
        "--course-id",
        required=True,
        help="safe course identifier to summarize",
    )


def _add_course_schedule_list_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
    )


def _add_course_schedule_save_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit local SQLite course schedule database",
    )
    parser.add_argument(
        "--course-id",
        required=True,
        help="safe course identifier to save",
    )
    parser.add_argument(
        "--title",
        required=True,
        help="course title to validate and store locally",
    )
    parser.add_argument(
        "--instructor-name",
        help="optional instructor name to validate and store locally",
    )
    parser.add_argument(
        "--meeting-url",
        help="optional meeting URL to validate and store locally",
    )
    parser.add_argument(
        "--meeting-label",
        help="optional meeting label to validate and store locally",
    )
    parser.add_argument(
        "--class-time",
        action="append",
        required=True,
        metavar="DAY,HH:MM,DURATION[,TIMEZONE][,LABEL]",
        help="repeatable class time metadata to validate and store locally",
    )


def _add_scheduled_start_preview_from_store_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe local session identifier to preview",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
    )
    parser.add_argument(
        "--course-id",
        required=True,
        help="safe course identifier to preview",
    )
    parser.add_argument(
        "--class-time-index",
        required=True,
        type=int,
        help="explicit zero-based stored class-time index to preview",
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
        help="preview the stored schedule as disabled",
    )


def _add_scheduled_start_next_from_store_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe local session identifier to preview",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
    )
    parser.add_argument(
        "--course-id",
        required=True,
        help="safe course identifier to preview",
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
        help="preview the next stored schedule as disabled",
    )


def _add_scheduled_start_due_list_from_store_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe local session identifier for the due list",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
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
        help="return disabled due-list metadata without due courses",
    )


def _add_session_stop_preview_from_store_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
    )
    parser.add_argument(
        "--course-id",
        required=True,
        help="safe course identifier to preview",
    )
    parser.add_argument(
        "--class-time-index",
        required=True,
        type=int,
        help="explicit zero-based stored class-time index to preview",
    )
    parser.add_argument(
        "--source-kind",
        required=True,
        choices=("file", "mic"),
        help="local source kind to preview",
    )
    parser.add_argument(
        "--disabled",
        action="store_true",
        help="preview the stored session stop as disabled",
    )


def _add_session_window_plan_from_store_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe local session identifier for the session window plan",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
    )
    parser.add_argument(
        "--source-kind",
        required=True,
        choices=("file", "mic"),
        help="local source kind to plan",
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
        help="return disabled session-window metadata without due courses",
    )


def _add_session_window_archive_preflight_from_store_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe local session identifier for the archive preflight",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit archive root containing the safe session directory",
    )
    parser.add_argument(
        "--source-kind",
        required=True,
        choices=("file", "mic"),
        help="local source kind to preflight",
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
        help="return disabled session-window archive metadata without due courses",
    )


def _add_session_window_alert_preview_from_store_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe local session identifier for the alert preview",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
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
        help="return disabled session-window alert metadata without due courses",
    )


def _add_session_window_readiness_preflight_from_store_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe local session identifier for the readiness preflight",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit archive root containing the safe session directory",
    )
    parser.add_argument(
        "--source-kind",
        required=True,
        choices=("file", "mic"),
        help="local source kind to preflight",
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
        help="return disabled session-window readiness metadata without due courses",
    )


def _add_session_window_confirmation_preflight_from_store_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe local session identifier for the confirmation preflight",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit archive root containing the safe session directory",
    )
    parser.add_argument(
        "--source-kind",
        required=True,
        choices=("file", "mic"),
        help="local source kind to preflight",
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
        help="return disabled session-window confirmation metadata without due courses",
    )


def _add_session_window_confirmation_response_from_store_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe local session identifier for the confirmation response",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit archive root containing the safe session directory",
    )
    parser.add_argument(
        "--source-kind",
        required=True,
        choices=("file", "mic"),
        help="local source kind to preflight",
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
        "--confirmation-response",
        required=True,
        choices=("confirmed", "declined"),
        help="fixed user response token to record",
    )
    parser.add_argument(
        "--disabled",
        action="store_true",
        help="return disabled session-window response metadata without due courses",
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


def _run_course_schedule_summary_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar course-schedule-summary-local",
        description=(
            "Summarize one stored local course schedule from an explicit "
            "read-only SQLite database path."
        ),
        fixed_error_message=_COURSE_SCHEDULE_SUMMARY_CLI_ERROR,
    )
    _add_course_schedule_summary_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_course_schedule_summary_local_command(args)


def _run_course_schedule_summary_local_command(args: argparse.Namespace) -> int:
    from async_scholar.schedule_store import (
        COURSE_SCHEDULE_SUMMARY_ERROR,
        load_course_schedule_safe_summary,
    )

    try:
        payload = load_course_schedule_safe_summary(
            args.db_path,
            args.course_id,
        )
    except ValueError:
        print(COURSE_SCHEDULE_SUMMARY_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _run_course_schedule_list_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar course-schedule-list-local",
        description=(
            "List stored local course schedule metadata from an explicit "
            "read-only SQLite database path."
        ),
        fixed_error_message=_COURSE_SCHEDULE_LIST_CLI_ERROR,
    )
    _add_course_schedule_list_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_course_schedule_list_local_command(args)


def _run_course_schedule_list_local_command(args: argparse.Namespace) -> int:
    from async_scholar.schedule_store import (
        COURSE_SCHEDULE_LIST_ERROR,
        list_course_schedule_safe_summaries,
    )

    try:
        payload = _course_schedule_list_safe_summary(
            list_course_schedule_safe_summaries(args.db_path)
        )
    except (KeyError, TypeError, ValueError):
        print(COURSE_SCHEDULE_LIST_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _course_schedule_list_safe_summary(payload: dict[str, object]) -> dict[str, object]:
    courses = payload["courses"]
    if not isinstance(courses, list):
        raise ValueError(_COURSE_SCHEDULE_LIST_CLI_ERROR)
    return {
        "course_count": payload["course_count"],
        "courses": [_course_schedule_safe_summary(course) for course in courses],
    }


def _run_course_schedule_save_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar course-schedule-save-local",
        description=(
            "Save one validated local course schedule into an explicit SQLite "
            "database path without executing a scheduler."
        ),
        fixed_error_message=_COURSE_SCHEDULE_SAVE_CLI_ERROR,
    )
    _add_course_schedule_save_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_course_schedule_save_local_command(args)


def _run_course_schedule_save_local_command(args: argparse.Namespace) -> int:
    from async_scholar.course_metadata import CourseMetadata
    from async_scholar.schedule_config import ScheduleConfig
    from async_scholar.schedule_store import save_course_schedule

    try:
        course_metadata = CourseMetadata(
            course_id=args.course_id,
            title=args.title,
            instructor_name=args.instructor_name,
            meeting_url=args.meeting_url,
            meeting_label=args.meeting_label,
        )
        schedule_config = ScheduleConfig(
            course_id=args.course_id,
            class_times=[
                _parse_course_schedule_class_time(class_time)
                for class_time in args.class_time
            ],
        )
        stored_schedule = save_course_schedule(
            args.db_path,
            course_metadata,
            schedule_config,
        )
        safe_payload = _course_schedule_safe_summary(stored_schedule.safe_summary())
    except (KeyError, TypeError, ValueError):
        print(_COURSE_SCHEDULE_SAVE_CLI_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(safe_payload, sort_keys=True))
    return 0


def _course_schedule_safe_summary(payload: dict[str, object]) -> dict[str, object]:
    return {key: payload[key] for key in _COURSE_SCHEDULE_SAFE_SUMMARY_KEYS}


def _parse_course_schedule_class_time(value: object) -> dict[str, object]:
    if not isinstance(value, str):
        raise ValueError(_COURSE_SCHEDULE_SAVE_CLI_ERROR)

    parts = value.split(",")
    if len(parts) < 3 or len(parts) > 5:
        raise ValueError(_COURSE_SCHEDULE_SAVE_CLI_ERROR)

    day_of_week, local_start_time, duration_text, *optional_parts = parts
    try:
        duration_minutes = int(duration_text)
    except ValueError:
        raise ValueError(_COURSE_SCHEDULE_SAVE_CLI_ERROR) from None

    class_time: dict[str, object] = {
        "day_of_week": day_of_week,
        "local_start_time": local_start_time,
        "duration_minutes": duration_minutes,
    }
    if optional_parts:
        class_time["timezone_name"] = optional_parts[0]
    if len(optional_parts) == 2:
        class_time["meeting_label"] = optional_parts[1]
    return class_time


def _run_scheduled_start_preview_from_store_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar scheduled-start-preview-from-store-local",
        description=(
            "Preview one non-executing scheduled-start decision from an "
            "explicit read-only local schedule store and explicit local clock."
        ),
        fixed_error_message=_SCHEDULED_START_PREVIEW_FROM_STORE_CLI_ERROR,
    )
    _add_scheduled_start_preview_from_store_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_scheduled_start_preview_from_store_local_command(args)


def _run_scheduled_start_preview_from_store_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.schedule_store import load_course_schedule_read_only
    from async_scholar.scheduled_start import (
        ScheduledStartClock,
        build_scheduled_start_manual_result,
        build_scheduled_start_plan,
        scheduled_start_manual_result_safe_summary,
    )

    try:
        stored_schedule = load_course_schedule_read_only(
            args.db_path,
            args.course_id,
        )
        plan = build_scheduled_start_plan(
            stored_schedule.schedule_config,
            selected_class_time_index=args.class_time_index,
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
        payload = _stored_schedule_preview_safe_summary(
            scheduled_start_manual_result_safe_summary(preview)
        )
    except (KeyError, TypeError, ValueError):
        print(_SCHEDULED_START_PREVIEW_FROM_STORE_CLI_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _stored_schedule_preview_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    return {key: payload[key] for key in _STORED_SCHEDULED_START_PREVIEW_KEYS}


def _run_scheduled_start_next_from_store_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar scheduled-start-next-from-store-local",
        description=(
            "Preview the next non-executing scheduled-start decision from an "
            "explicit read-only local schedule store and explicit local clock."
        ),
        fixed_error_message=_SCHEDULED_START_NEXT_FROM_STORE_CLI_ERROR,
    )
    _add_scheduled_start_next_from_store_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_scheduled_start_next_from_store_local_command(args)


def _run_scheduled_start_next_from_store_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.schedule_store import load_course_schedule_read_only
    from async_scholar.scheduled_start import (
        ScheduledStartClock,
        build_next_scheduled_start_preview_summary,
    )

    try:
        stored_schedule = load_course_schedule_read_only(
            args.db_path,
            args.course_id,
        )
        clock = ScheduledStartClock(
            day_of_week=args.clock_day_of_week,
            local_time=args.clock_local_time,
        )
        payload = _stored_schedule_next_preview_safe_summary(
            build_next_scheduled_start_preview_summary(
                stored_schedule.schedule_config,
                clock,
                args.session_id,
                args.source_kind,
                enabled=not args.disabled,
            )
        )
    except (KeyError, TypeError, ValueError):
        print(_SCHEDULED_START_NEXT_FROM_STORE_CLI_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _stored_schedule_next_preview_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    return {key: payload[key] for key in _STORED_SCHEDULED_START_NEXT_PREVIEW_KEYS}


def _run_scheduled_start_due_list_from_store_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar scheduled-start-due-list-from-store-local",
        description=(
            "List due non-executing scheduled-start metadata from an explicit "
            "read-only local schedule store and explicit local clock."
        ),
        fixed_error_message=_SCHEDULED_START_DUE_LIST_FROM_STORE_CLI_ERROR,
    )
    _add_scheduled_start_due_list_from_store_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_scheduled_start_due_list_from_store_local_command(args)


def _run_scheduled_start_due_list_from_store_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.schedule_store import list_course_schedule_due_list_inputs
    from async_scholar.scheduled_start import (
        ScheduledStartClock,
        build_scheduled_start_due_list_summary,
    )

    try:
        clock = ScheduledStartClock(
            day_of_week=args.clock_day_of_week,
            local_time=args.clock_local_time,
        )
        payload = _stored_schedule_due_list_safe_summary(
            build_scheduled_start_due_list_summary(
                list_course_schedule_due_list_inputs(args.db_path),
                clock,
                args.session_id,
                args.source_kind,
                enabled=not args.disabled,
            )
        )
    except (KeyError, TypeError, ValueError):
        print(_SCHEDULED_START_DUE_LIST_FROM_STORE_CLI_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _stored_schedule_due_list_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    courses = payload["courses"]
    if not isinstance(courses, list):
        raise ValueError(_SCHEDULED_START_DUE_LIST_FROM_STORE_CLI_ERROR)
    safe_payload = {key: payload[key] for key in _STORED_SCHEDULED_START_DUE_LIST_KEYS}
    safe_payload["courses"] = [
        _stored_schedule_due_list_course_safe_summary(course) for course in courses
    ]
    return safe_payload


def _stored_schedule_due_list_course_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    return {key: payload[key] for key in _STORED_SCHEDULED_START_DUE_LIST_COURSE_KEYS}


def _run_session_stop_preview_from_store_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-stop-preview-from-store-local",
        description=(
            "Preview one non-executing session-stop decision from an explicit "
            "read-only local schedule store."
        ),
        fixed_error_message=_SESSION_STOP_PREVIEW_FROM_STORE_CLI_ERROR,
    )
    _add_session_stop_preview_from_store_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_stop_preview_from_store_local_command(args)


def _run_session_stop_preview_from_store_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.schedule_store import load_course_schedule_session_stop_input
    from async_scholar.session_stop import build_session_stop_preview_from_store_input

    try:
        payload = _stored_session_stop_preview_safe_summary(
            build_session_stop_preview_from_store_input(
                load_course_schedule_session_stop_input(
                    args.db_path,
                    args.course_id,
                    args.class_time_index,
                ),
                args.source_kind,
                enabled=not args.disabled,
            )
        )
    except (KeyError, TypeError, ValueError):
        print(_SESSION_STOP_PREVIEW_FROM_STORE_CLI_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _stored_session_stop_preview_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    return {key: payload[key] for key in _STORED_SESSION_STOP_PREVIEW_KEYS}


def _run_session_window_plan_from_store_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-plan-from-store-local",
        description=(
            "Build due non-executing session-window metadata from an explicit "
            "read-only local schedule store and explicit local clock."
        ),
        fixed_error_message=_SESSION_WINDOW_PLAN_FROM_STORE_CLI_ERROR,
    )
    _add_session_window_plan_from_store_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_plan_from_store_local_command(args)


def _run_session_window_plan_from_store_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.schedule_store import list_course_schedule_session_window_inputs
    from async_scholar.scheduled_start import ScheduledStartClock
    from async_scholar.session_window import build_stored_session_window_plan_summary

    try:
        clock = ScheduledStartClock(
            day_of_week=args.clock_day_of_week,
            local_time=args.clock_local_time,
        )
        payload = _stored_session_window_plan_safe_summary(
            build_stored_session_window_plan_summary(
                list_course_schedule_session_window_inputs(args.db_path),
                clock,
                args.session_id,
                args.source_kind,
                enabled=not args.disabled,
            )
        )
    except (KeyError, TypeError, ValueError):
        print(_SESSION_WINDOW_PLAN_FROM_STORE_CLI_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _stored_session_window_plan_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    courses = payload["courses"]
    if not isinstance(courses, list):
        raise ValueError(_SESSION_WINDOW_PLAN_FROM_STORE_CLI_ERROR)
    safe_payload = {key: payload[key] for key in _STORED_SESSION_WINDOW_PLAN_KEYS}
    safe_payload["courses"] = [
        _stored_session_window_plan_course_safe_summary(course) for course in courses
    ]
    return safe_payload


def _stored_session_window_plan_course_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    return {key: payload[key] for key in _STORED_SESSION_WINDOW_PLAN_COURSE_KEYS}


def _run_session_window_archive_preflight_from_store_local_argv(
    argv: list[str],
) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-archive-preflight-from-store-local",
        description=(
            "Build read-only session-window archive preflight metadata from an "
            "explicit read-only local schedule store, archive root, and local clock."
        ),
        fixed_error_message=_SESSION_WINDOW_ARCHIVE_PREFLIGHT_FROM_STORE_CLI_ERROR,
    )
    _add_session_window_archive_preflight_from_store_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_archive_preflight_from_store_local_command(args)


def _run_session_window_archive_preflight_from_store_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.schedule_store import list_course_schedule_session_window_inputs
    from async_scholar.scheduled_start import ScheduledStartClock
    from async_scholar.session_window_archive_preflight import (
        build_session_window_archive_preflight_summary,
    )

    try:
        clock = ScheduledStartClock(
            day_of_week=args.clock_day_of_week,
            local_time=args.clock_local_time,
        )
        payload = _stored_session_window_archive_preflight_safe_summary(
            build_session_window_archive_preflight_summary(
                list_course_schedule_session_window_inputs(args.db_path),
                args.archive_root,
                args.session_id,
                args.source_kind,
                clock,
                enabled=not args.disabled,
            )
        )
    except (KeyError, TypeError, ValueError):
        print(
            _SESSION_WINDOW_ARCHIVE_PREFLIGHT_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _stored_session_window_archive_preflight_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    courses = payload["courses"]
    if not isinstance(courses, list):
        raise ValueError(_SESSION_WINDOW_ARCHIVE_PREFLIGHT_FROM_STORE_CLI_ERROR)
    safe_payload = {
        key: payload[key] for key in _STORED_SESSION_WINDOW_ARCHIVE_PREFLIGHT_KEYS
    }
    safe_payload["courses"] = [
        _stored_session_window_archive_preflight_course_safe_summary(course)
        for course in courses
    ]
    return safe_payload


def _stored_session_window_archive_preflight_course_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    return {
        key: payload[key]
        for key in _STORED_SESSION_WINDOW_ARCHIVE_PREFLIGHT_COURSE_KEYS
    }


def _run_session_window_alert_preview_from_store_local_argv(
    argv: list[str],
) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-alert-preview-from-store-local",
        description=(
            "Build metadata-only session-window alert preview data from an "
            "explicit read-only local schedule store and explicit local clock."
        ),
        fixed_error_message=_SESSION_WINDOW_ALERT_PREVIEW_FROM_STORE_CLI_ERROR,
    )
    _add_session_window_alert_preview_from_store_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_alert_preview_from_store_local_command(args)


def _run_session_window_alert_preview_from_store_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.schedule_store import list_course_schedule_session_window_inputs
    from async_scholar.scheduled_start import ScheduledStartClock
    from async_scholar.session_window_alert_preview import (
        build_session_window_alert_preview_summary,
    )

    try:
        clock = ScheduledStartClock(
            day_of_week=args.clock_day_of_week,
            local_time=args.clock_local_time,
        )
        payload = _stored_session_window_alert_preview_safe_summary(
            build_session_window_alert_preview_summary(
                list_course_schedule_session_window_inputs(args.db_path),
                args.session_id,
                args.source_kind,
                clock,
                enabled=not args.disabled,
            )
        )
    except (KeyError, TypeError, ValueError):
        print(
            _SESSION_WINDOW_ALERT_PREVIEW_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _stored_session_window_alert_preview_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    courses = payload["courses"]
    if not isinstance(courses, list):
        raise ValueError(_SESSION_WINDOW_ALERT_PREVIEW_FROM_STORE_CLI_ERROR)
    safe_payload = {
        key: payload[key] for key in _STORED_SESSION_WINDOW_ALERT_PREVIEW_KEYS
    }
    safe_payload["courses"] = [
        _stored_session_window_alert_preview_course_safe_summary(course)
        for course in courses
    ]
    return safe_payload


def _stored_session_window_alert_preview_course_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    safe_payload = {
        key: payload[key] for key in _STORED_SESSION_WINDOW_ALERT_PREVIEW_COURSE_KEYS
    }
    alert_preview = safe_payload["alert_preview"]
    if not isinstance(alert_preview, dict):
        raise ValueError(_SESSION_WINDOW_ALERT_PREVIEW_FROM_STORE_CLI_ERROR)
    safe_payload["alert_preview"] = {
        key: alert_preview[key]
        for key in _STORED_SESSION_WINDOW_ALERT_PREVIEW_METADATA_KEYS
    }
    if safe_payload["alert_preview"] != _STORED_SESSION_WINDOW_ALERT_PREVIEW_METADATA:
        raise ValueError(_SESSION_WINDOW_ALERT_PREVIEW_FROM_STORE_CLI_ERROR)
    return safe_payload


def _run_session_window_readiness_preflight_from_store_local_argv(
    argv: list[str],
) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-readiness-preflight-from-store-local",
        description=(
            "Build read-only session-window readiness preflight metadata from an "
            "explicit read-only local schedule store, archive root, and local clock."
        ),
        fixed_error_message=_SESSION_WINDOW_READINESS_PREFLIGHT_FROM_STORE_CLI_ERROR,
    )
    _add_session_window_readiness_preflight_from_store_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_readiness_preflight_from_store_local_command(args)


def _run_session_window_readiness_preflight_from_store_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.schedule_store import list_course_schedule_session_window_inputs
    from async_scholar.scheduled_start import ScheduledStartClock
    from async_scholar.session_window_readiness_preflight import (
        build_session_window_readiness_preflight_summary,
    )

    try:
        clock = ScheduledStartClock(
            day_of_week=args.clock_day_of_week,
            local_time=args.clock_local_time,
        )
        payload = _stored_session_window_readiness_preflight_safe_summary(
            build_session_window_readiness_preflight_summary(
                list_course_schedule_session_window_inputs(args.db_path),
                args.archive_root,
                args.session_id,
                args.source_kind,
                clock,
                enabled=not args.disabled,
            )
        )
    except (KeyError, TypeError, ValueError):
        print(
            _SESSION_WINDOW_READINESS_PREFLIGHT_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _stored_session_window_readiness_preflight_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    courses = payload["courses"]
    if not isinstance(courses, list):
        raise ValueError(_SESSION_WINDOW_READINESS_PREFLIGHT_FROM_STORE_CLI_ERROR)
    safe_payload = {
        key: payload[key] for key in _STORED_SESSION_WINDOW_READINESS_PREFLIGHT_KEYS
    }
    safe_payload["courses"] = [
        _stored_session_window_readiness_preflight_course_safe_summary(course)
        for course in courses
    ]
    return safe_payload


def _stored_session_window_readiness_preflight_course_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    safe_payload = {
        key: payload[key]
        for key in _STORED_SESSION_WINDOW_READINESS_PREFLIGHT_COURSE_KEYS
    }
    alert_preview = safe_payload["alert_preview"]
    if not isinstance(alert_preview, dict):
        raise ValueError(_SESSION_WINDOW_READINESS_PREFLIGHT_FROM_STORE_CLI_ERROR)
    safe_payload["alert_preview"] = {
        key: alert_preview[key]
        for key in _STORED_SESSION_WINDOW_ALERT_PREVIEW_METADATA_KEYS
    }
    if safe_payload["alert_preview"] != _STORED_SESSION_WINDOW_ALERT_PREVIEW_METADATA:
        raise ValueError(_SESSION_WINDOW_READINESS_PREFLIGHT_FROM_STORE_CLI_ERROR)
    return safe_payload


def _run_session_window_confirmation_preflight_from_store_local_argv(
    argv: list[str],
) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-confirmation-preflight-from-store-local",
        description=(
            "Build read-only session-window confirmation preflight metadata from an "
            "explicit read-only local schedule store, archive root, and local clock."
        ),
        fixed_error_message=_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_FROM_STORE_CLI_ERROR,
    )
    _add_session_window_confirmation_preflight_from_store_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_confirmation_preflight_from_store_local_command(args)


def _run_session_window_confirmation_preflight_from_store_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.schedule_store import list_course_schedule_session_window_inputs
    from async_scholar.scheduled_start import ScheduledStartClock
    from async_scholar.session_window_confirmation_preflight import (
        build_session_window_confirmation_preflight_summary,
    )

    try:
        clock = ScheduledStartClock(
            day_of_week=args.clock_day_of_week,
            local_time=args.clock_local_time,
        )
        payload = _stored_session_window_confirmation_preflight_safe_summary(
            build_session_window_confirmation_preflight_summary(
                list_course_schedule_session_window_inputs(args.db_path),
                args.archive_root,
                args.session_id,
                args.source_kind,
                clock,
                enabled=not args.disabled,
            )
        )
    except (KeyError, TypeError, ValueError):
        print(
            _SESSION_WINDOW_CONFIRMATION_PREFLIGHT_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _stored_session_window_confirmation_preflight_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    courses = payload["courses"]
    if not isinstance(courses, list):
        raise ValueError(_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_FROM_STORE_CLI_ERROR)
    safe_payload = {
        key: payload[key] for key in _STORED_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_KEYS
    }
    if safe_payload["status"] != safe_payload["confirmation_status"]:
        raise ValueError(_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_FROM_STORE_CLI_ERROR)
    if (
        safe_payload["confirmation_status"]
        not in _STORED_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_STATUSES
    ):
        raise ValueError(_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_FROM_STORE_CLI_ERROR)
    safe_payload["courses"] = [
        _stored_session_window_confirmation_preflight_course_safe_summary(course)
        for course in courses
    ]
    if not safe_payload["confirmation_required"] and (
        safe_payload["blocked_execution_count"] != 0 or safe_payload["courses"]
    ):
        raise ValueError(_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_FROM_STORE_CLI_ERROR)
    if safe_payload["confirmation_required"] and (
        safe_payload["blocked_execution_count"] != safe_payload["due_count"]
        or any(
            not course["requires_confirmation"] for course in safe_payload["courses"]
        )
    ):
        raise ValueError(_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_FROM_STORE_CLI_ERROR)
    return safe_payload


def _stored_session_window_confirmation_preflight_course_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    return {
        key: payload[key]
        for key in _STORED_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_COURSE_KEYS
    }


def _run_session_window_confirmation_response_from_store_local_argv(
    argv: list[str],
) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-confirmation-response-from-store-local",
        description=(
            "Build non-executing session-window confirmation response metadata from "
            "an explicit read-only local schedule store, archive root, local clock, "
            "and fixed confirmation response."
        ),
        fixed_error_message=_SESSION_WINDOW_CONFIRMATION_RESPONSE_FROM_STORE_CLI_ERROR,
    )
    _add_session_window_confirmation_response_from_store_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_confirmation_response_from_store_local_command(args)


def _run_session_window_confirmation_response_from_store_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.schedule_store import list_course_schedule_session_window_inputs
    from async_scholar.scheduled_start import ScheduledStartClock
    from async_scholar.session_window_confirmation_preflight import (
        build_session_window_confirmation_preflight_summary,
    )
    from async_scholar.session_window_confirmation_response import (
        build_session_window_confirmation_response_summary,
    )

    try:
        clock = ScheduledStartClock(
            day_of_week=args.clock_day_of_week,
            local_time=args.clock_local_time,
        )
        preflight_payload = build_session_window_confirmation_preflight_summary(
            list_course_schedule_session_window_inputs(args.db_path),
            args.archive_root,
            args.session_id,
            args.source_kind,
            clock,
            enabled=not args.disabled,
        )
        payload = _stored_session_window_confirmation_response_safe_summary(
            build_session_window_confirmation_response_summary(
                preflight_payload,
                args.confirmation_response,
            )
        )
    except (KeyError, TypeError, ValueError):
        print(
            _SESSION_WINDOW_CONFIRMATION_RESPONSE_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _stored_session_window_confirmation_response_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    courses = payload["courses"]
    if not isinstance(courses, list):
        raise ValueError(_SESSION_WINDOW_CONFIRMATION_RESPONSE_FROM_STORE_CLI_ERROR)
    safe_payload = {
        key: payload[key] for key in _STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_KEYS
    }
    if (
        safe_payload["status"]
        not in _STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_STATUSES
    ):
        raise ValueError(_SESSION_WINDOW_CONFIRMATION_RESPONSE_FROM_STORE_CLI_ERROR)
    if (
        safe_payload["confirmation_response"]
        not in _STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_TOKENS
    ):
        raise ValueError(_SESSION_WINDOW_CONFIRMATION_RESPONSE_FROM_STORE_CLI_ERROR)
    safe_payload["courses"] = [
        _stored_session_window_confirmation_response_course_safe_summary(
            course,
            safe_payload["confirmation_response"],
        )
        for course in courses
    ]
    if (
        safe_payload["status"] in ("disabled", "not_required")
        and safe_payload["courses"]
    ):
        raise ValueError(_SESSION_WINDOW_CONFIRMATION_RESPONSE_FROM_STORE_CLI_ERROR)
    return safe_payload


def _stored_session_window_confirmation_response_course_safe_summary(
    payload: dict[str, object],
    confirmation_response: object,
) -> dict[str, object]:
    safe_payload = {
        key: payload[key]
        for key in _STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_COURSE_KEYS
    }
    if safe_payload["confirmation_response"] != confirmation_response:
        raise ValueError(_SESSION_WINDOW_CONFIRMATION_RESPONSE_FROM_STORE_CLI_ERROR)
    return safe_payload


def _run_mic_recording_diagnostic_command(argv: list[str]) -> int:
    from async_scholar.audio.mic_recording_diagnostic import (
        main as run_mic_recording_diagnostic,
    )

    return run_mic_recording_diagnostic(argv)


if __name__ == "__main__":
    raise SystemExit(main())
