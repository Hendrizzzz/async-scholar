from __future__ import annotations

import inspect
import json
import sqlite3
import subprocess
import sys
import types
from pathlib import Path

import pytest

from async_scholar import __main__ as cli
from async_scholar.course_metadata import CourseMetadata
from async_scholar.schedule_config import ScheduleConfig
from async_scholar.schedule_store import (
    initialize_course_schedule_store,
    load_course_schedule_read_only,
    save_course_schedule,
)


def _write_private_course_schedule(db_path: Path) -> None:
    save_course_schedule(
        db_path,
        CourseMetadata(
            course_id="cs101",
            title="Confidential Systems",
            instructor_name="Dr. Private",
            meeting_url="https://meet.example.edu/class-room?token=private",
            meeting_label="Private lecture",
        ),
        ScheduleConfig(
            course_id="cs101",
            class_times=[
                {
                    "day_of_week": "monday",
                    "local_start_time": "09:00",
                    "duration_minutes": 75,
                    "timezone_name": "Asia/Manila",
                    "meeting_label": "Private lecture",
                },
                {
                    "day_of_week": "wednesday",
                    "local_start_time": "13:30",
                    "duration_minutes": 90,
                    "timezone_name": "Asia/Manila",
                    "meeting_label": "Private lab",
                },
            ],
        ),
    )


def test_module_help_prints_useful_output() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "async_scholar", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar" in result.stdout
    assert "local-first lecture monitoring" in result.stdout
    assert "--version" in result.stdout
    assert "crash-recovery-preflight" in result.stdout
    assert "archive-export-preflight" in result.stdout
    assert "archive-export-local" in result.stdout
    assert "archive-export-verify-local" in result.stdout
    assert "archive-delete-dry-run-local" in result.stdout
    assert "scheduled-start-preview-local" in result.stdout
    assert "course-schedule-summary-local" in result.stdout
    assert "course-schedule-list-local" in result.stdout
    assert "course-schedule-save-local" in result.stdout
    assert "scheduled-start-preview-from-store-local" in result.stdout
    assert "scheduled-start-next-from-store-local" in result.stdout
    assert "scheduled-start-due-list-from-store-local" in result.stdout
    assert "session-stop-preview-from-store-local" in result.stdout
    assert "session-window-plan-from-store-local" in result.stdout
    assert "session-window-archive-preflight-from-store-local" in result.stdout
    assert "session-window-alert-preview-from-store-local" in result.stdout
    assert "session-window-readiness-preflight-from-store-local" in result.stdout
    assert "session-window-confirmation-preflight-from-store-local" in result.stdout
    assert "session-window-confirmation-response-from-store-local" in result.stdout
    assert "session-window-start-authorization-from-store-local" in result.stdout
    assert "session-window-start-receipt-from-store-local" in result.stdout
    assert "session-window-stop-receipt-from-store-local" in result.stdout
    assert "session-window-runtime-summary-local" in result.stdout
    assert "session-window-recovery-decision-local" in result.stdout
    assert "session-window-recovery-review-local" in result.stdout
    assert "mic-recording-diagnostic" in result.stdout


def test_mic_recording_diagnostic_help_prints_existing_options() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "mic-recording-diagnostic",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "--output-root" in result.stdout
    assert "--seconds" in result.stdout
    assert "--max-chunks" in result.stdout
    assert "--device-id" in result.stdout


def test_build_parser_does_not_import_mic_recording_diagnostic(
    monkeypatch,
) -> None:
    module_name = "async_scholar.audio.mic_recording_diagnostic"
    monkeypatch.delitem(sys.modules, module_name, raising=False)

    cli.build_parser()

    assert module_name not in sys.modules


def test_crash_recovery_preflight_help_does_not_build_preflight(
    monkeypatch,
) -> None:
    module_name = "async_scholar.session_recovery"
    monkeypatch.delitem(sys.modules, module_name, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "crash-recovery-preflight",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar crash-recovery-preflight" in result.stdout
    assert "--sessions-root" in result.stdout
    assert "metadata" in result.stdout
    assert module_name not in sys.modules


def test_crash_recovery_preflight_requires_explicit_sessions_root() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "crash-recovery-preflight",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr == "crash recovery session preflight could not be built\n"


def test_crash_recovery_preflight_sanitizes_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "crash-recovery-preflight",
            "session-001",
            "C:\\Users\\student\\token-secret-auth-profile",
            "--sessions-root",
            ".",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "crash recovery session preflight could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "unrecognized arguments",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_crash_recovery_preflight_sanitizes_misordered_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--sessions-root",
            "C:\\Users\\student\\token-secret-auth-profile",
            "crash-recovery-preflight",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "crash recovery session preflight could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "invalid choice",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_crash_recovery_preflight_sanitizes_equals_form_parent_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--sessions-root=C:\\Users\\student\\token-secret-auth-profile",
            "fixture-demo",
            "tests/fixtures/transcripts/attendance_roll_call.jsonl",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "crash recovery session preflight could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "invalid choice",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_crash_recovery_preflight_command_prints_safe_json(tmp_path) -> None:
    session_dir = tmp_path / "session-001"
    session_dir.mkdir()
    transcript_text = "Synthetic transcript token secret auth profile payload."
    event_text = "Synthetic event private payload."
    alert_text = "Synthetic alert private payload."
    reviewer_text = "Synthetic reviewer private payload."
    (session_dir / "transcript.jsonl").write_text(
        transcript_text,
        encoding="utf-8",
    )
    (session_dir / "events.jsonl").write_text(event_text, encoding="utf-8")
    (session_dir / "alerts.log").write_text(alert_text, encoding="utf-8")
    (session_dir / "reviewer.md").write_text(reviewer_text, encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "crash-recovery-preflight",
            "session-001",
            "--sessions-root",
            str(tmp_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.count("\n") == 1
    payload = json.loads(result.stdout)
    assert payload["preflight_kind"] == "crash_recovery_session_preflight"
    assert payload["session_id"] == "session-001"
    assert payload["session_dir"] == "session-001"
    assert payload["recovery_status"] == "partial"
    assert payload["existing_count"] == 4
    assert payload["missing_count"] == 3
    assert payload["total_existing_size_bytes"] == sum(
        len(text.encode("utf-8"))
        for text in (transcript_text, event_text, alert_text, reviewer_text)
    )
    assert [artifact["filename"] for artifact in payload["artifacts"]] == [
        "transcript.jsonl",
        "transcript.md",
        "events.jsonl",
        "alerts.log",
        "reviewer.md",
        "runtime.jsonl",
        "benchmark-report.json",
    ]

    combined_output = f"{result.stdout}\n{result.stderr}".lower()
    for forbidden_fragment in (
        str(tmp_path).lower(),
        "synthetic transcript",
        "synthetic event",
        "synthetic alert",
        "synthetic reviewer",
        "token",
        "secret",
        "auth",
        "profile",
        "payload",
        "repair",
        "delete",
        "scheduler",
        "traceback",
    ):
        assert forbidden_fragment not in combined_output


def test_crash_recovery_preflight_command_sanitizes_failures(tmp_path) -> None:
    unsafe_root = tmp_path / "root-token-secret-auth-profile"
    unsafe_root.write_text("Synthetic private root placeholder.", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "crash-recovery-preflight",
            "session-001",
            "--sessions-root",
            str(unsafe_root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "crash recovery session preflight could not be built\n"
    for forbidden_fragment in (
        str(tmp_path),
        "root-token",
        "secret",
        "auth",
        "profile",
        "Synthetic private",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_archive_export_preflight_help_does_not_build_preflight(
    monkeypatch,
) -> None:
    module_name = "async_scholar.archive_export"
    monkeypatch.delitem(sys.modules, module_name, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-export-preflight",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar archive-export-preflight" in result.stdout
    assert "--archive-root" in result.stdout
    assert "metadata" in result.stdout
    assert module_name not in sys.modules


def test_archive_export_preflight_requires_explicit_archive_root() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-export-preflight",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr == "archive export preflight could not be built\n"


def test_archive_export_preflight_sanitizes_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-export-preflight",
            "session-001",
            "C:\\Users\\student\\token-secret-auth-profile",
            "--archive-root",
            ".",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "archive export preflight could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "unrecognized arguments",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_archive_export_preflight_sanitizes_misordered_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--archive-root",
            "C:\\Users\\student\\token-secret-auth-profile",
            "archive-export-preflight",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "archive export preflight could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "invalid choice",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_archive_export_preflight_sanitizes_equals_form_parent_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--archive-root=C:\\Users\\student\\token-secret-auth-profile",
            "fixture-demo",
            "tests/fixtures/transcripts/attendance_roll_call.jsonl",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "archive export preflight could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "invalid choice",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_archive_export_preflight_command_prints_safe_json(tmp_path) -> None:
    session_dir = tmp_path / "session-001"
    session_dir.mkdir()
    transcript_text = "Synthetic transcript token secret auth profile payload."
    event_text = "Synthetic event private payload."
    alert_text = "Synthetic alert private payload."
    reviewer_text = "Synthetic reviewer private payload."
    (session_dir / "transcript.jsonl").write_text(
        transcript_text,
        encoding="utf-8",
    )
    (session_dir / "events.jsonl").write_text(event_text, encoding="utf-8")
    (session_dir / "alerts.log").write_text(alert_text, encoding="utf-8")
    (session_dir / "reviewer.md").write_text(reviewer_text, encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-export-preflight",
            "session-001",
            "--archive-root",
            str(tmp_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.count("\n") == 1
    payload = json.loads(result.stdout)
    assert payload["session_id"] == "session-001"
    assert payload["session_dir"] == "session-001"
    assert payload["existing_count"] == 4
    assert payload["missing_count"] == 3
    assert payload["total_existing_size_bytes"] == sum(
        len(text.encode("utf-8"))
        for text in (transcript_text, event_text, alert_text, reviewer_text)
    )
    assert [artifact["filename"] for artifact in payload["artifacts"]] == [
        "transcript.jsonl",
        "transcript.md",
        "events.jsonl",
        "alerts.log",
        "reviewer.md",
        "runtime.jsonl",
        "benchmark-report.json",
    ]

    combined_output = f"{result.stdout}\n{result.stderr}".lower()
    for forbidden_fragment in (
        str(tmp_path).lower(),
        "synthetic transcript",
        "synthetic event",
        "synthetic alert",
        "synthetic reviewer",
        "token",
        "secret",
        "auth",
        "profile",
        "payload",
        "copy",
        "delete",
        "scheduler",
        "traceback",
    ):
        assert forbidden_fragment not in combined_output


def test_archive_export_preflight_command_sanitizes_failures(tmp_path) -> None:
    unsafe_root = tmp_path / "root-token-secret-auth-profile"
    unsafe_root.write_text("Synthetic private root placeholder.", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-export-preflight",
            "session-001",
            "--archive-root",
            str(unsafe_root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "archive export preflight could not be built\n"
    for forbidden_fragment in (
        str(tmp_path),
        "root-token",
        "secret",
        "auth",
        "profile",
        "Synthetic private",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_archive_export_preflight_command_delegates_to_existing_helpers(
    capsys,
    monkeypatch,
) -> None:
    received: dict[str, object] = {}
    module_name = "async_scholar.archive_export"
    fake_module = types.ModuleType(module_name)
    fake_preflight = object()

    def fake_build(archive_root: Path, session_id: str) -> object:
        received["archive_root"] = archive_root
        received["session_id"] = session_id
        return fake_preflight

    def fake_summary(preflight: object) -> dict[str, object]:
        received["preflight"] = preflight
        return {"session_id": "session-001", "existing_count": 0}

    fake_module.build_archive_export_preflight_summary_from_root = fake_build
    fake_module.archive_export_preflight_summary_safe_summary = fake_summary
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    exit_code = cli.main(
        [
            "archive-export-preflight",
            "session-001",
            "--archive-root",
            "archive-root",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out) == {
        "existing_count": 0,
        "session_id": "session-001",
    }
    assert captured.err == ""
    assert received == {
        "archive_root": Path("archive-root"),
        "session_id": "session-001",
        "preflight": fake_preflight,
    }


def test_archive_export_local_help_does_not_execute_export(
    monkeypatch,
) -> None:
    module_name = "async_scholar.archive_export"
    monkeypatch.delitem(sys.modules, module_name, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-export-local",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar archive-export-local" in result.stdout
    assert "--archive-root" in result.stdout
    assert "--export-root" in result.stdout
    assert module_name not in sys.modules


def test_archive_export_local_requires_explicit_roots() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-export-local",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr == "archive export could not be executed\n"


def test_archive_export_local_sanitizes_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-export-local",
            "session-001",
            "C:\\Users\\student\\token-secret-auth-profile",
            "--archive-root",
            ".",
            "--export-root",
            ".",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "archive export could not be executed\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "unrecognized arguments",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_archive_export_local_sanitizes_misordered_archive_root_failure() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--archive-root",
            "C:\\Users\\student\\token-secret-auth-profile",
            "archive-export-local",
            "session-001",
            "--export-root",
            ".",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "archive export could not be executed\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "invalid choice",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_archive_export_local_sanitizes_misordered_export_root_failure() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--export-root=C:\\Users\\student\\token-secret-auth-profile",
            "fixture-demo",
            "tests/fixtures/transcripts/attendance_roll_call.jsonl",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "archive export could not be executed\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "invalid choice",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_archive_export_local_command_prints_safe_json_and_copies_allowed_files(
    tmp_path,
) -> None:
    archive_root = tmp_path / "archive"
    export_root = tmp_path / "export"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    export_root.mkdir()
    transcript_text = "Synthetic transcript token secret auth profile payload."
    event_text = "Synthetic event private payload."
    alert_text = "Synthetic alert private payload."
    reviewer_text = "Synthetic reviewer private payload."
    (session_dir / "transcript.jsonl").write_text(
        transcript_text,
        encoding="utf-8",
    )
    (session_dir / "events.jsonl").write_text(event_text, encoding="utf-8")
    (session_dir / "alerts.log").write_text(alert_text, encoding="utf-8")
    (session_dir / "reviewer.md").write_text(reviewer_text, encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-export-local",
            "session-001",
            "--archive-root",
            str(archive_root),
            "--export-root",
            str(export_root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.count("\n") == 1
    payload = json.loads(result.stdout)
    assert payload["session_id"] == "session-001"
    assert payload["session_dir"] == "session-001"
    assert payload["export_dir"] == "session-001"
    assert payload["artifact_count"] == 4
    assert payload["total_exported_size_bytes"] == sum(
        len(text.encode("utf-8"))
        for text in (transcript_text, event_text, alert_text, reviewer_text)
    )
    assert [artifact["filename"] for artifact in payload["artifacts"]] == [
        "transcript.jsonl",
        "events.jsonl",
        "alerts.log",
        "reviewer.md",
    ]
    assert all(artifact["status"] == "exported" for artifact in payload["artifacts"])
    exported_session_dir = export_root / "session-001"
    for filename in (
        "transcript.jsonl",
        "events.jsonl",
        "alerts.log",
        "reviewer.md",
    ):
        assert (exported_session_dir / filename).is_file()

    combined_output = f"{result.stdout}\n{result.stderr}".lower()
    for forbidden_fragment in (
        str(tmp_path).lower(),
        "synthetic transcript",
        "synthetic event",
        "synthetic alert",
        "synthetic reviewer",
        "token",
        "secret",
        "auth",
        "profile",
        "payload",
        "scheduler",
        "traceback",
        "gate d",
    ):
        assert forbidden_fragment not in combined_output


def test_archive_export_local_command_sanitizes_failures(tmp_path) -> None:
    archive_root = tmp_path / "archive"
    unsafe_export_root = tmp_path / "export-token-secret-auth-profile"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    unsafe_export_root.write_text(
        "Synthetic private export placeholder.",
        encoding="utf-8",
    )
    (session_dir / "events.jsonl").write_text("{}", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-export-local",
            "session-001",
            "--archive-root",
            str(archive_root),
            "--export-root",
            str(unsafe_export_root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "archive export could not be executed\n"
    for forbidden_fragment in (
        str(tmp_path),
        "export-token",
        "secret",
        "auth",
        "profile",
        "Synthetic private",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_archive_export_local_command_delegates_to_existing_helpers(
    capsys,
    monkeypatch,
) -> None:
    received: dict[str, object] = {}
    module_name = "async_scholar.archive_export"
    fake_module = types.ModuleType(module_name)
    fake_result = object()

    def fake_execute(archive_root: Path, export_root: Path, session_id: str) -> object:
        received["archive_root"] = archive_root
        received["export_root"] = export_root
        received["session_id"] = session_id
        return fake_result

    def fake_summary(export_result: object) -> dict[str, object]:
        received["export_result"] = export_result
        return {"artifact_count": 0, "session_id": "session-001"}

    fake_module.execute_archive_export_to_local_root = fake_execute
    fake_module.archive_export_execution_result_safe_summary = fake_summary
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    exit_code = cli.main(
        [
            "archive-export-local",
            "session-001",
            "--archive-root",
            "archive-root",
            "--export-root",
            "export-root",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out) == {
        "artifact_count": 0,
        "session_id": "session-001",
    }
    assert captured.err == ""
    assert received == {
        "archive_root": Path("archive-root"),
        "export_root": Path("export-root"),
        "session_id": "session-001",
        "export_result": fake_result,
    }


def test_archive_export_verify_local_help_does_not_build_verification(
    monkeypatch,
) -> None:
    module_name = "async_scholar.archive_export"
    monkeypatch.delitem(sys.modules, module_name, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-export-verify-local",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar archive-export-verify-local" in result.stdout
    assert "--archive-root" in result.stdout
    assert "--export-root" in result.stdout
    assert module_name not in sys.modules


def test_archive_export_verify_local_requires_explicit_roots() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-export-verify-local",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr == "archive export verification could not be built\n"


def test_archive_export_verify_local_sanitizes_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-export-verify-local",
            "session-001",
            "C:\\Users\\student\\token-secret-auth-profile",
            "--archive-root",
            ".",
            "--export-root",
            ".",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "archive export verification could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "unrecognized arguments",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_archive_export_verify_local_sanitizes_misordered_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--archive-root",
            "C:\\Users\\student\\token-secret-auth-profile",
            "archive-export-verify-local",
            "session-001",
            "--export-root",
            ".",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "archive export verification could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "invalid choice",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_archive_export_verify_local_command_prints_safe_json(tmp_path) -> None:
    archive_root = tmp_path / "archive-token-secret-auth-profile"
    export_root = tmp_path / "export-token-secret-auth-profile"
    session_dir = archive_root / "session-001"
    exported_session_dir = export_root / "session-001"
    session_dir.mkdir(parents=True)
    exported_session_dir.mkdir(parents=True)
    event_text = "Synthetic event token secret auth profile payload."
    reviewer_text = "Synthetic reviewer private payload."
    (session_dir / "events.jsonl").write_text(event_text, encoding="utf-8")
    (session_dir / "reviewer.md").write_text(reviewer_text, encoding="utf-8")
    (exported_session_dir / "events.jsonl").write_text(event_text, encoding="utf-8")
    (exported_session_dir / "reviewer.md").write_text(
        reviewer_text,
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-export-verify-local",
            "session-001",
            "--archive-root",
            str(archive_root),
            "--export-root",
            str(export_root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.count("\n") == 1
    payload = json.loads(result.stdout)
    assert payload["session_id"] == "session-001"
    assert payload["session_dir"] == "session-001"
    assert payload["export_dir"] == "session-001"
    assert payload["expected_count"] == 2
    assert payload["verified_count"] == 2
    assert payload["all_verified"] is True
    assert [artifact["filename"] for artifact in payload["artifacts"]] == [
        "transcript.jsonl",
        "transcript.md",
        "events.jsonl",
        "alerts.log",
        "reviewer.md",
        "runtime.jsonl",
        "benchmark-report.json",
    ]
    assert payload["artifacts"][2]["status"] == "verified"
    assert payload["artifacts"][4]["status"] == "verified"

    combined_output = f"{result.stdout}\n{result.stderr}".lower()
    for forbidden_fragment in (
        str(tmp_path).lower(),
        "archive-token",
        "export-token",
        "synthetic event",
        "synthetic reviewer",
        "token",
        "secret",
        "auth",
        "profile",
        "payload",
        "traceback",
        "gate d",
    ):
        assert forbidden_fragment not in combined_output


def test_archive_export_verify_local_command_sanitizes_failures(tmp_path) -> None:
    archive_root = tmp_path / "archive-token-secret-auth-profile"
    export_root = tmp_path / "export-token-secret-auth-profile"
    archive_root.write_text("Synthetic private archive placeholder.", encoding="utf-8")
    export_root.mkdir()

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-export-verify-local",
            "session-001",
            "--archive-root",
            str(archive_root),
            "--export-root",
            str(export_root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "archive export verification could not be built\n"
    for forbidden_fragment in (
        str(tmp_path),
        "archive-token",
        "export-token",
        "secret",
        "auth",
        "profile",
        "Synthetic private",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_archive_export_verify_local_command_delegates_to_existing_helpers(
    capsys,
    monkeypatch,
) -> None:
    received: dict[str, object] = {}
    module_name = "async_scholar.archive_export"
    fake_module = types.ModuleType(module_name)
    fake_verification = object()

    def fake_build(archive_root: Path, export_root: Path, session_id: str) -> object:
        received["archive_root"] = archive_root
        received["export_root"] = export_root
        received["session_id"] = session_id
        return fake_verification

    def fake_summary(verification: object) -> dict[str, object]:
        received["verification"] = verification
        return {"all_verified": True, "session_id": "session-001"}

    fake_module.build_archive_export_verification_summary_from_roots = fake_build
    fake_module.archive_export_verification_summary_safe_summary = fake_summary
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    exit_code = cli.main(
        [
            "archive-export-verify-local",
            "session-001",
            "--archive-root",
            "archive-root",
            "--export-root",
            "export-root",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out) == {
        "all_verified": True,
        "session_id": "session-001",
    }
    assert captured.err == ""
    assert received == {
        "archive_root": Path("archive-root"),
        "export_root": Path("export-root"),
        "session_id": "session-001",
        "verification": fake_verification,
    }


def test_archive_delete_dry_run_local_help_does_not_build_dry_run(
    monkeypatch,
) -> None:
    module_name = "async_scholar.archive_delete_dry_run_result"
    monkeypatch.delitem(sys.modules, module_name, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-delete-dry-run-local",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar archive-delete-dry-run-local" in result.stdout
    assert "--archive-root" in result.stdout
    assert "dry run" in result.stdout
    assert module_name not in sys.modules


def test_archive_delete_dry_run_local_requires_explicit_archive_root() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-delete-dry-run-local",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr == "archive delete dry run could not be built\n"


def test_archive_delete_dry_run_local_sanitizes_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-delete-dry-run-local",
            "session-001",
            "C:\\Users\\student\\token-secret-auth-profile",
            "--archive-root",
            ".",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "archive delete dry run could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "unrecognized arguments",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_archive_delete_dry_run_local_sanitizes_misordered_archive_root_failure() -> (
    None
):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--archive-root",
            "C:\\Users\\student\\token-secret-auth-profile",
            "archive-delete-dry-run-local",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "archive delete dry run could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "invalid choice",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_archive_delete_dry_run_local_command_prints_safe_json(tmp_path) -> None:
    archive_root = tmp_path / "archive-token-secret-auth-profile"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    event_text = "Synthetic event token secret auth profile payload."
    reviewer_text = "Synthetic reviewer private payload."
    (session_dir / "events.jsonl").write_text(event_text, encoding="utf-8")
    (session_dir / "reviewer.md").write_text(reviewer_text, encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-delete-dry-run-local",
            "session-001",
            "--archive-root",
            str(archive_root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.count("\n") == 1
    payload = json.loads(result.stdout)
    assert payload["session_id"] == "session-001"
    assert payload["session_dir"] == "session-001"
    assert payload["result_kind"] == "archive_delete_dry_run_result"
    assert payload["status"] == "dry_run_completed"
    assert payload["dry_run_only"] is True
    assert payload["deletion_performed"] is False
    assert payload["artifact_count"] == 7
    assert payload["existing_artifact_count"] == 2
    assert payload["total_existing_size_bytes"] == sum(
        len(text.encode("utf-8")) for text in (event_text, reviewer_text)
    )
    assert [artifact["filename"] for artifact in payload["artifacts"]] == [
        "transcript.jsonl",
        "transcript.md",
        "events.jsonl",
        "alerts.log",
        "reviewer.md",
        "runtime.jsonl",
        "benchmark-report.json",
    ]
    assert payload["artifacts"][2]["exists"] is True
    assert payload["artifacts"][2]["size_bytes"] == len(event_text.encode("utf-8"))
    assert payload["artifacts"][4]["exists"] is True
    assert payload["artifacts"][4]["size_bytes"] == len(reviewer_text.encode("utf-8"))
    assert all(artifact["status"] == "not_deleted" for artifact in payload["artifacts"])

    combined_output = f"{result.stdout}\n{result.stderr}".lower()
    for forbidden_fragment in (
        str(tmp_path).lower(),
        "archive-token",
        "synthetic event",
        "synthetic reviewer",
        "token",
        "secret",
        "auth",
        "profile",
        "payload",
        "traceback",
        "gate d",
    ):
        assert forbidden_fragment not in combined_output


def test_archive_delete_dry_run_local_command_sanitizes_failures(tmp_path) -> None:
    unsafe_root = tmp_path / "archive-token-secret-auth-profile"
    unsafe_root.write_text("Synthetic private archive placeholder.", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-delete-dry-run-local",
            "session-001",
            "--archive-root",
            str(unsafe_root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "archive delete dry run could not be built\n"
    for forbidden_fragment in (
        str(tmp_path),
        "archive-token",
        "secret",
        "auth",
        "profile",
        "Synthetic private",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_archive_delete_dry_run_local_command_delegates_to_existing_helpers(
    capsys,
    monkeypatch,
) -> None:
    received: dict[str, object] = {}
    module_name = "async_scholar.archive_delete_dry_run_result"
    fake_module = types.ModuleType(module_name)
    fake_dry_run = object()

    def fake_build(archive_root: Path, session_id: str) -> object:
        received["archive_root"] = archive_root
        received["session_id"] = session_id
        return fake_dry_run

    def fake_export(dry_run: object) -> dict[str, object]:
        received["dry_run"] = dry_run
        return {
            "deletion_performed": False,
            "dry_run_only": True,
            "session_id": "session-001",
        }

    fake_module.ARCHIVE_DELETE_DRY_RUN_LOCAL_ERROR = (
        "archive delete dry run could not be built"
    )
    fake_module.build_archive_delete_dry_run_local_result = fake_build
    fake_module.export_archive_delete_dry_run_local_result = fake_export
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    exit_code = cli.main(
        [
            "archive-delete-dry-run-local",
            "session-001",
            "--archive-root",
            "archive-root",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out) == {
        "deletion_performed": False,
        "dry_run_only": True,
        "session_id": "session-001",
    }
    assert captured.err == ""
    assert received == {
        "archive_root": Path("archive-root"),
        "session_id": "session-001",
        "dry_run": fake_dry_run,
    }


def test_scheduled_start_preview_local_help_stays_lazy(
    monkeypatch,
) -> None:
    schedule_config_module = "async_scholar.schedule_config"
    scheduled_start_module = "async_scholar.scheduled_start"
    monkeypatch.delitem(sys.modules, schedule_config_module, raising=False)
    monkeypatch.delitem(sys.modules, scheduled_start_module, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-preview-local",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar scheduled-start-preview-local" in result.stdout
    assert "--course-id" in result.stdout
    assert "--clock-local-time" in result.stdout
    assert "non-executing" in result.stdout
    assert schedule_config_module not in sys.modules
    assert scheduled_start_module not in sys.modules


def test_scheduled_start_preview_local_requires_explicit_metadata() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-preview-local",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr == "scheduled start preview could not be built\n"


def test_scheduled_start_preview_local_sanitizes_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-preview-local",
            "session-001",
            "C:\\Users\\student\\token-secret-auth-profile",
            "--course-id",
            "cs101",
            "--day-of-week",
            "monday",
            "--local-start-time",
            "09:00",
            "--duration-minutes",
            "75",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "scheduled start preview could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "unrecognized arguments",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_scheduled_start_preview_local_sanitizes_misordered_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--course-id",
            "C:\\Users\\student\\token-secret-auth-profile",
            "scheduled-start-preview-local",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "scheduled start preview could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "invalid choice",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_scheduled_start_preview_local_command_prints_due_safe_json() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-preview-local",
            "session-001",
            "--course-id",
            "cs101",
            "--day-of-week",
            "monday",
            "--local-start-time",
            "09:00",
            "--duration-minutes",
            "75",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.count("\n") == 1
    payload = json.loads(result.stdout)
    assert payload == {
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_id": "cs101",
        "due": True,
        "enabled": True,
        "minutes_until_start": 0,
        "next_day_of_week": "monday",
        "next_local_start_time": "09:00",
        "result_kind": "scheduled_start_manual_result",
        "scheduled_day_of_week": "monday",
        "scheduled_local_start_time": "09:00",
        "session_id": "session-001",
        "source_kind": "file",
        "status": "due",
    }
    _assert_scheduled_start_preview_output_is_safe(result.stdout, result.stderr)


def test_scheduled_start_preview_local_command_prints_waiting_safe_json() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-preview-local",
            "session-001",
            "--course-id",
            "cs101",
            "--day-of-week",
            "monday",
            "--local-start-time",
            "09:00",
            "--duration-minutes",
            "75",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "08:30",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["status"] == "waiting"
    assert payload["due"] is False
    assert payload["enabled"] is True
    assert payload["minutes_until_start"] == 30
    assert payload["next_day_of_week"] == "monday"
    assert payload["next_local_start_time"] == "09:00"
    _assert_scheduled_start_preview_output_is_safe(result.stdout, result.stderr)


def test_scheduled_start_preview_local_command_prints_disabled_safe_json() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-preview-local",
            "session-001",
            "--course-id",
            "cs101",
            "--day-of-week",
            "monday",
            "--local-start-time",
            "09:00",
            "--duration-minutes",
            "75",
            "--source-kind",
            "mic",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
            "--disabled",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["status"] == "disabled"
    assert payload["source_kind"] == "mic"
    assert payload["enabled"] is False
    assert payload["due"] is False
    assert payload["minutes_until_start"] is None
    assert payload["next_day_of_week"] is None
    assert payload["next_local_start_time"] is None
    _assert_scheduled_start_preview_output_is_safe(result.stdout, result.stderr)


def test_scheduled_start_preview_local_command_sanitizes_build_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-preview-local",
            "C:\\Users\\student\\token-secret-auth-profile",
            "--course-id",
            "cs101",
            "--day-of-week",
            "monday",
            "--local-start-time",
            "09:00",
            "--duration-minutes",
            "75",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "scheduled start preview could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "ValidationError",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_scheduled_start_preview_local_command_delegates_to_existing_helpers(
    capsys,
    monkeypatch,
) -> None:
    received: dict[str, object] = {}
    schedule_config_module = "async_scholar.schedule_config"
    scheduled_start_module = "async_scholar.scheduled_start"
    fake_schedule_config_module = types.ModuleType(schedule_config_module)
    fake_scheduled_start_module = types.ModuleType(scheduled_start_module)
    fake_config = object()
    fake_plan = object()
    fake_clock = object()
    fake_preview = object()

    class FakeScheduleConfig:
        def __new__(cls, **kwargs: object) -> object:
            received["schedule_config_kwargs"] = kwargs
            return fake_config

    def fake_build_plan(
        schedule_config: object,
        selected_class_time_index: int,
        source_kind: str,
        *,
        enabled: bool,
    ) -> object:
        received["plan_config"] = schedule_config
        received["selected_class_time_index"] = selected_class_time_index
        received["source_kind"] = source_kind
        received["enabled"] = enabled
        return fake_plan

    class FakeClock:
        def __new__(cls, **kwargs: object) -> object:
            received["clock_kwargs"] = kwargs
            return fake_clock

    def fake_build_manual_result(
        plan: object,
        clock: object,
        session_id: str,
    ) -> object:
        received["manual_plan"] = plan
        received["manual_clock"] = clock
        received["session_id"] = session_id
        return fake_preview

    def fake_summary(preview: object) -> dict[str, object]:
        received["preview"] = preview
        return {"session_id": "session-001", "status": "due"}

    fake_schedule_config_module.ScheduleConfig = FakeScheduleConfig
    fake_scheduled_start_module.ScheduledStartClock = FakeClock
    fake_scheduled_start_module.build_scheduled_start_plan = fake_build_plan
    fake_scheduled_start_module.build_scheduled_start_manual_result = (
        fake_build_manual_result
    )
    fake_scheduled_start_module.scheduled_start_manual_result_safe_summary = (
        fake_summary
    )
    monkeypatch.setitem(
        sys.modules,
        schedule_config_module,
        fake_schedule_config_module,
    )
    monkeypatch.setitem(
        sys.modules,
        scheduled_start_module,
        fake_scheduled_start_module,
    )

    exit_code = cli.main(
        [
            "scheduled-start-preview-local",
            "session-001",
            "--course-id",
            "cs101",
            "--day-of-week",
            "monday",
            "--local-start-time",
            "09:00",
            "--duration-minutes",
            "75",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out) == {"session_id": "session-001", "status": "due"}
    assert captured.err == ""
    assert received == {
        "schedule_config_kwargs": {
            "course_id": "cs101",
            "class_times": [
                {
                    "day_of_week": "monday",
                    "local_start_time": "09:00",
                    "duration_minutes": 75,
                }
            ],
        },
        "plan_config": fake_config,
        "selected_class_time_index": 0,
        "source_kind": "file",
        "enabled": True,
        "clock_kwargs": {"day_of_week": "monday", "local_time": "09:00"},
        "manual_plan": fake_plan,
        "manual_clock": fake_clock,
        "session_id": "session-001",
        "preview": fake_preview,
    }


def test_course_schedule_save_local_help_stays_lazy(monkeypatch) -> None:
    module_names = (
        "async_scholar.course_metadata",
        "async_scholar.schedule_config",
        "async_scholar.schedule_store",
    )
    for module_name in module_names:
        monkeypatch.delitem(sys.modules, module_name, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "course-schedule-save-local",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar course-schedule-save-local" in result.stdout
    assert "--db-path" in result.stdout
    assert "--class-time" in result.stdout
    assert "without executing" in result.stdout
    for module_name in module_names:
        assert module_name not in sys.modules


def test_course_schedule_save_local_requires_explicit_metadata() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "course-schedule-save-local",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr == "course schedule save could not be built\n"


def test_course_schedule_save_local_sanitizes_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "course-schedule-save-local",
            "C:\\Users\\student\\token-secret-auth-profile",
            "--db-path",
            "schedule.sqlite",
            "--course-id",
            "cs101",
            "--title",
            "Private Title",
            "--class-time",
            "monday,09:00,75",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "course schedule save could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "unrecognized arguments",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_course_schedule_save_local_sanitizes_misordered_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--db-path",
            "C:\\Users\\student\\token-secret-auth-profile",
            "course-schedule-save-local",
            "--course-id",
            "cs101",
            "--title",
            "Private Title",
            "--class-time",
            "monday,09:00,75",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "course schedule save could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "invalid choice",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_course_schedule_save_local_command_prints_safe_json(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "course-schedule-save-local",
            "--db-path",
            str(db_path),
            "--course-id",
            "CS101",
            "--title",
            "Confidential Systems",
            "--instructor-name",
            "Dr. Private",
            "--meeting-url",
            "https://meet.example.edu/class-room?token=private",
            "--meeting-label",
            "Private lecture",
            "--class-time",
            "monday,09:00,75,Asia/Manila,Private lecture",
            "--class-time",
            "wednesday,13:30,90,Asia/Manila,Private lab",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.count("\n") == 1
    assert json.loads(result.stdout) == {
        "class_time_count": 2,
        "course_id": "cs101",
    }
    stored_schedule = load_course_schedule_read_only(db_path, "cs101")
    assert stored_schedule.class_time_count == 2
    assert stored_schedule.course_metadata.meeting_url is not None
    _assert_course_schedule_save_output_is_safe(result.stdout, result.stderr)


def test_course_schedule_save_local_command_updates_existing_schedule(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    base_command = [
        sys.executable,
        "-m",
        "async_scholar",
        "course-schedule-save-local",
        "--db-path",
        str(db_path),
        "--course-id",
        "cs101",
        "--title",
        "Private Title",
    ]

    first = subprocess.run(
        [
            *base_command,
            "--class-time",
            "monday,09:00,75",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    second = subprocess.run(
        [
            *base_command,
            "--class-time",
            "monday,09:00,75",
            "--class-time",
            "thursday,18:45,105",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert first.returncode == 0
    assert second.returncode == 0
    assert json.loads(first.stdout) == {
        "class_time_count": 1,
        "course_id": "cs101",
    }
    assert json.loads(second.stdout) == {
        "class_time_count": 2,
        "course_id": "cs101",
    }
    assert load_course_schedule_read_only(db_path, "cs101").class_time_count == 2
    _assert_course_schedule_save_output_is_safe(first.stdout, first.stderr)
    _assert_course_schedule_save_output_is_safe(second.stdout, second.stderr)


def test_course_schedule_save_local_missing_parent_fails_safely(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "missing-token-secret-auth-profile" / "schedule.sqlite"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "course-schedule-save-local",
            "--db-path",
            str(db_path),
            "--course-id",
            "cs101",
            "--title",
            "Private Title",
            "--class-time",
            "monday,09:00,75",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "course schedule save could not be built\n"
    assert not db_path.parent.exists()
    assert not db_path.exists()
    for forbidden_fragment in (
        str(tmp_path),
        "missing-token",
        "secret",
        "auth",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_course_schedule_save_local_sanitizes_invalid_metadata(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "course-schedule-save-local",
            "--db-path",
            str(db_path),
            "--course-id",
            "cs101",
            "--title",
            "Private Title",
            "--meeting-url",
            "file:///C:/Users/student/token-secret-auth-profile",
            "--class-time",
            "monday,09:00,75",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "course schedule save could not be built\n"
    assert not db_path.exists()
    for forbidden_fragment in (
        "file:",
        "C:/Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_course_schedule_save_local_sanitizes_invalid_class_time(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "course-schedule-save-local",
            "--db-path",
            str(db_path),
            "--course-id",
            "cs101",
            "--title",
            "Private Title",
            "--class-time",
            "monday,25:99,duration-token-secret",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "course schedule save could not be built\n"
    assert not db_path.exists()
    for forbidden_fragment in (
        str(tmp_path),
        "25:99",
        "duration",
        "token",
        "secret",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_course_schedule_save_local_command_delegates_to_existing_models(
    capsys,
    monkeypatch,
) -> None:
    received: dict[str, object] = {}
    course_metadata_module = "async_scholar.course_metadata"
    schedule_config_module = "async_scholar.schedule_config"
    schedule_store_module = "async_scholar.schedule_store"
    fake_course_metadata_module = types.ModuleType(course_metadata_module)
    fake_schedule_config_module = types.ModuleType(schedule_config_module)
    fake_schedule_store_module = types.ModuleType(schedule_store_module)
    fake_course_metadata = object()
    fake_schedule_config = object()

    class FakeCourseMetadata:
        def __new__(cls, **kwargs: object) -> object:
            received["course_metadata_kwargs"] = kwargs
            return fake_course_metadata

    class FakeScheduleConfig:
        def __new__(cls, **kwargs: object) -> object:
            received["schedule_config_kwargs"] = kwargs
            return fake_schedule_config

    class FakeStoredSchedule:
        def safe_summary(self) -> dict[str, object]:
            received["safe_summary_called"] = True
            return {"class_time_count": 2, "course_id": "cs101"}

    def fake_save(
        db_path: Path,
        course_metadata: object,
        schedule_config: object,
    ) -> object:
        received["db_path"] = db_path
        received["course_metadata"] = course_metadata
        received["schedule_config"] = schedule_config
        return FakeStoredSchedule()

    fake_course_metadata_module.CourseMetadata = FakeCourseMetadata
    fake_schedule_config_module.ScheduleConfig = FakeScheduleConfig
    fake_schedule_store_module.save_course_schedule = fake_save
    monkeypatch.setitem(
        sys.modules,
        course_metadata_module,
        fake_course_metadata_module,
    )
    monkeypatch.setitem(
        sys.modules,
        schedule_config_module,
        fake_schedule_config_module,
    )
    monkeypatch.setitem(sys.modules, schedule_store_module, fake_schedule_store_module)

    exit_code = cli.main(
        [
            "course-schedule-save-local",
            "--db-path",
            "schedule.sqlite",
            "--course-id",
            "cs101",
            "--title",
            "Private Title",
            "--instructor-name",
            "Dr. Private",
            "--meeting-url",
            "https://meet.example.edu/class-room?token=private",
            "--meeting-label",
            "Private lecture",
            "--class-time",
            "monday,09:00,75,Asia/Manila,Private lecture",
            "--class-time",
            "wednesday,13:30,90,Asia/Manila,Private lab",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out) == {
        "class_time_count": 2,
        "course_id": "cs101",
    }
    assert captured.err == ""
    assert received == {
        "course_metadata_kwargs": {
            "course_id": "cs101",
            "title": "Private Title",
            "instructor_name": "Dr. Private",
            "meeting_url": "https://meet.example.edu/class-room?token=private",
            "meeting_label": "Private lecture",
        },
        "schedule_config_kwargs": {
            "course_id": "cs101",
            "class_times": [
                {
                    "day_of_week": "monday",
                    "local_start_time": "09:00",
                    "duration_minutes": 75,
                    "timezone_name": "Asia/Manila",
                    "meeting_label": "Private lecture",
                },
                {
                    "day_of_week": "wednesday",
                    "local_start_time": "13:30",
                    "duration_minutes": 90,
                    "timezone_name": "Asia/Manila",
                    "meeting_label": "Private lab",
                },
            ],
        },
        "db_path": Path("schedule.sqlite"),
        "course_metadata": fake_course_metadata,
        "schedule_config": fake_schedule_config,
        "safe_summary_called": True,
    }


def test_course_schedule_save_local_handler_stays_bounded() -> None:
    source = "\n".join(
        [
            inspect.getsource(cli._run_course_schedule_save_local_command),
            inspect.getsource(cli._parse_course_schedule_class_time),
        ]
    )

    assert "CourseMetadata" in source
    assert "ScheduleConfig" in source
    assert "save_course_schedule" in source
    for forbidden_fragment in (
        "load_course_schedule_read_only",
        "load_course_schedule(",
        "initialize_course_schedule_store",
        "datetime",
        "now(",
        "sleep",
        "Timer(",
        "threading",
        "subprocess",
        "webbrowser",
        "requests",
        "httpx",
        "playwright",
        "sounddevice",
        "telegram",
        "desktop_notifier",
        "execute_archive",
        "archive_export",
        ".open(",
        ".read_text(",
        ".write_text(",
        ".mkdir(",
        ".unlink(",
        ".remove(",
        ".rmdir(",
    ):
        assert forbidden_fragment not in source


def test_course_schedule_summary_local_help_stays_lazy(
    monkeypatch,
) -> None:
    module_name = "async_scholar.schedule_store"
    monkeypatch.delitem(sys.modules, module_name, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "course-schedule-summary-local",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar course-schedule-summary-local" in result.stdout
    assert "--db-path" in result.stdout
    assert "--course-id" in result.stdout
    assert "read-only" in result.stdout
    assert module_name not in sys.modules


def test_course_schedule_summary_local_requires_explicit_metadata() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "course-schedule-summary-local",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr == "course schedule summary could not be built\n"


def test_course_schedule_summary_local_sanitizes_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "course-schedule-summary-local",
            "C:\\Users\\student\\token-secret-auth-profile",
            "--db-path",
            "schedule.sqlite",
            "--course-id",
            "cs101",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "course schedule summary could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "unrecognized arguments",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_course_schedule_summary_local_sanitizes_misordered_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--db-path",
            "C:\\Users\\student\\token-secret-auth-profile",
            "course-schedule-summary-local",
            "--course-id",
            "cs101",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "course schedule summary could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "invalid choice",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_course_schedule_summary_local_command_prints_safe_json(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "course-schedule-summary-local",
            "--db-path",
            str(db_path),
            "--course-id",
            "cs101",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.count("\n") == 1
    assert json.loads(result.stdout) == {
        "class_time_count": 2,
        "course_id": "cs101",
    }
    _assert_course_schedule_summary_output_is_safe(result.stdout, result.stderr)


def test_course_schedule_summary_local_missing_db_does_not_create_file(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "missing-token-secret-auth-profile.sqlite"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "course-schedule-summary-local",
            "--db-path",
            str(db_path),
            "--course-id",
            "cs101",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "course schedule summary could not be built\n"
    assert not db_path.exists()
    for forbidden_fragment in (
        str(tmp_path),
        "missing-token",
        "secret",
        "auth",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_course_schedule_summary_local_command_sanitizes_missing_course(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "course-schedule-summary-local",
            "--db-path",
            str(db_path),
            "--course-id",
            "missing-token-secret-auth-profile",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "course schedule summary could not be built\n"
    for forbidden_fragment in (
        str(tmp_path),
        "missing",
        "token",
        "secret",
        "auth",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_course_schedule_summary_local_command_delegates_to_read_only_summary(
    capsys,
    monkeypatch,
) -> None:
    received: dict[str, object] = {}
    module_name = "async_scholar.schedule_store"
    fake_module = types.ModuleType(module_name)

    def fake_summary(db_path: Path, course_id: str) -> dict[str, object]:
        received["db_path"] = db_path
        received["course_id"] = course_id
        return {"course_id": "cs101", "class_time_count": 2}

    fake_module.COURSE_SCHEDULE_SUMMARY_ERROR = (
        "course schedule summary could not be built"
    )
    fake_module.load_course_schedule_safe_summary = fake_summary
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    exit_code = cli.main(
        [
            "course-schedule-summary-local",
            "--db-path",
            "schedule.sqlite",
            "--course-id",
            "cs101",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out) == {
        "class_time_count": 2,
        "course_id": "cs101",
    }
    assert captured.err == ""
    assert received == {
        "db_path": Path("schedule.sqlite"),
        "course_id": "cs101",
    }


def test_course_schedule_summary_local_handler_stays_read_only() -> None:
    source = inspect.getsource(cli._run_course_schedule_summary_local_command)

    assert "load_course_schedule_safe_summary" in source
    for forbidden_fragment in (
        "load_course_schedule(",
        "save_course_schedule",
        "initialize_course_schedule_store",
        "_create_schema",
        "ScheduleConfig",
        "CourseMetadata",
        "datetime",
        "now(",
        "sleep",
        "Timer(",
        "threading",
        "subprocess",
        "webbrowser",
        "requests",
        "httpx",
        "playwright",
        "sounddevice",
        "telegram",
        "desktop_notifier",
        "execute_archive",
        "archive_export",
        ".open(",
        ".read_text(",
        ".write_text(",
        ".mkdir(",
        ".unlink(",
        ".remove(",
        ".rmdir(",
    ):
        assert forbidden_fragment not in source


def test_course_schedule_list_local_help_stays_lazy(
    monkeypatch,
) -> None:
    module_name = "async_scholar.schedule_store"
    monkeypatch.delitem(sys.modules, module_name, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "course-schedule-list-local",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar course-schedule-list-local" in result.stdout
    assert "--db-path" in result.stdout
    assert "read-only" in result.stdout
    assert module_name not in sys.modules


def test_course_schedule_list_local_requires_explicit_db_path() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "course-schedule-list-local",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr == "course schedule list could not be built\n"


def test_course_schedule_list_local_sanitizes_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "course-schedule-list-local",
            "C:\\Users\\student\\token-secret-auth-profile",
            "--db-path",
            "schedule.sqlite",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "course schedule list could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "unrecognized arguments",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_course_schedule_list_local_sanitizes_misordered_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--db-path",
            "C:\\Users\\student\\token-secret-auth-profile",
            "course-schedule-list-local",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "course schedule list could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "invalid choice",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_course_schedule_list_local_command_prints_safe_json(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)
    save_course_schedule(
        db_path,
        CourseMetadata(
            course_id="math101",
            title="Private Math",
            instructor_name="Dr. Secret",
            meeting_url="https://meet.example.edu/math?token=secret",
            meeting_label="Private math lecture",
        ),
        ScheduleConfig(
            course_id="math101",
            class_times=[
                {
                    "day_of_week": "friday",
                    "local_start_time": "14:00",
                    "duration_minutes": 60,
                    "timezone_name": "Asia/Manila",
                    "meeting_label": "Private math lecture",
                }
            ],
        ),
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "course-schedule-list-local",
            "--db-path",
            str(db_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.count("\n") == 1
    assert json.loads(result.stdout) == {
        "course_count": 2,
        "courses": [
            {"class_time_count": 2, "course_id": "cs101"},
            {"class_time_count": 1, "course_id": "math101"},
        ],
    }
    _assert_course_schedule_list_output_is_safe(result.stdout, result.stderr)


def test_course_schedule_list_local_missing_db_does_not_create_file(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "missing-token-secret-auth-profile.sqlite"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "course-schedule-list-local",
            "--db-path",
            str(db_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "course schedule list could not be built\n"
    assert not db_path.exists()
    for forbidden_fragment in (
        str(tmp_path),
        "missing-token",
        "secret",
        "auth",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_course_schedule_list_local_command_sanitizes_malformed_store(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE courses (course_id TEXT PRIMARY KEY)")
        connection.execute("INSERT INTO courses (course_id) VALUES (?)", ("cs101",))

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "course-schedule-list-local",
            "--db-path",
            str(db_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "course schedule list could not be built\n"
    for forbidden_fragment in (
        str(tmp_path),
        "class_times",
        "select",
        "sqlite",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_course_schedule_list_local_command_delegates_to_read_only_list(
    capsys,
    monkeypatch,
) -> None:
    received: dict[str, object] = {}
    module_name = "async_scholar.schedule_store"
    fake_module = types.ModuleType(module_name)

    def fake_list(db_path: Path) -> dict[str, object]:
        received["db_path"] = db_path
        return {
            "course_count": 1,
            "courses": [
                {
                    "course_id": "cs101",
                    "class_time_count": 2,
                    "meeting_url": "https://meet.example.edu/token-secret",
                }
            ],
            "private_title": "Confidential Systems",
        }

    fake_module.COURSE_SCHEDULE_LIST_ERROR = "course schedule list could not be built"
    fake_module.list_course_schedule_safe_summaries = fake_list
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    exit_code = cli.main(
        [
            "course-schedule-list-local",
            "--db-path",
            "schedule.sqlite",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out) == {
        "course_count": 1,
        "courses": [{"class_time_count": 2, "course_id": "cs101"}],
    }
    assert captured.err == ""
    assert received == {"db_path": Path("schedule.sqlite")}
    _assert_course_schedule_list_output_is_safe(captured.out, captured.err)


def test_course_schedule_list_local_handler_stays_read_only() -> None:
    source = inspect.getsource(cli._run_course_schedule_list_local_command)

    assert "list_course_schedule_safe_summaries" in source
    for forbidden_fragment in (
        "load_course_schedule(",
        "load_course_schedule_read_only",
        "load_course_schedule_safe_summary",
        "save_course_schedule",
        "initialize_course_schedule_store",
        "_create_schema",
        "ScheduleConfig",
        "CourseMetadata",
        "build_scheduled_start",
        "ScheduledStartClock",
        "datetime",
        "now(",
        "sleep",
        "Timer(",
        "threading",
        "asyncio",
        "subprocess",
        "webbrowser",
        "requests",
        "httpx",
        "playwright",
        "selenium",
        "sounddevice",
        "faster_whisper",
        "mic_recording",
        "telegram",
        "desktop_notifier",
        "execute_archive",
        "archive_export",
        "archive_delete",
        ".open(",
        ".read_text(",
        ".write_text(",
        ".mkdir(",
        ".unlink(",
        ".remove(",
        ".rmdir(",
        "rmtree",
    ):
        assert forbidden_fragment not in source


def test_scheduled_start_preview_from_store_local_help_stays_lazy(
    monkeypatch,
) -> None:
    schedule_store_module = "async_scholar.schedule_store"
    scheduled_start_module = "async_scholar.scheduled_start"
    monkeypatch.delitem(sys.modules, schedule_store_module, raising=False)
    monkeypatch.delitem(sys.modules, scheduled_start_module, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-preview-from-store-local",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar scheduled-start-preview-from-store-local" in (
        result.stdout
    )
    assert "--db-path" in result.stdout
    assert "--class-time-index" in result.stdout
    assert "--clock-local-time" in result.stdout
    assert "non-executing" in result.stdout
    assert schedule_store_module not in sys.modules
    assert scheduled_start_module not in sys.modules


def test_scheduled_start_preview_from_store_local_requires_explicit_metadata() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-preview-from-store-local",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr == "stored scheduled start preview could not be built\n"


def test_scheduled_start_preview_from_store_local_sanitizes_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-preview-from-store-local",
            "session-001",
            "C:\\Users\\student\\token-secret-auth-profile",
            "--db-path",
            "schedule.sqlite",
            "--course-id",
            "cs101",
            "--class-time-index",
            "0",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "stored scheduled start preview could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "unrecognized arguments",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_scheduled_start_preview_from_store_local_sanitizes_misordered_failures() -> (
    None
):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--db-path",
            "C:\\Users\\student\\token-secret-auth-profile",
            "scheduled-start-preview-from-store-local",
            "session-001",
            "--course-id",
            "cs101",
            "--class-time-index",
            "0",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "stored scheduled start preview could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "invalid choice",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_scheduled_start_preview_from_store_local_command_prints_safe_json(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-preview-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--course-id",
            "cs101",
            "--class-time-index",
            "1",
            "--source-kind",
            "mic",
            "--clock-day-of-week",
            "wednesday",
            "--clock-local-time",
            "13:30",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.count("\n") == 1
    assert json.loads(result.stdout) == {
        "clock_day_of_week": "wednesday",
        "clock_local_time": "13:30",
        "course_id": "cs101",
        "due": True,
        "minutes_until_start": 0,
        "next_day_of_week": "wednesday",
        "next_local_start_time": "13:30",
        "scheduled_day_of_week": "wednesday",
        "scheduled_local_start_time": "13:30",
        "session_id": "session-001",
        "source_kind": "mic",
        "status": "due",
    }
    _assert_stored_schedule_preview_output_is_safe(result.stdout, result.stderr)


def test_scheduled_start_preview_from_store_local_command_prints_disabled_json(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-preview-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--course-id",
            "cs101",
            "--class-time-index",
            "0",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
            "--disabled",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload == {
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_id": "cs101",
        "due": False,
        "minutes_until_start": None,
        "next_day_of_week": None,
        "next_local_start_time": None,
        "scheduled_day_of_week": "monday",
        "scheduled_local_start_time": "09:00",
        "session_id": "session-001",
        "source_kind": "file",
        "status": "disabled",
    }
    assert "enabled" not in payload
    assert "result_kind" not in payload
    _assert_stored_schedule_preview_output_is_safe(result.stdout, result.stderr)


def test_scheduled_start_preview_from_store_local_missing_db_does_not_create_file(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "missing-token-secret-auth-profile.sqlite"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-preview-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--course-id",
            "cs101",
            "--class-time-index",
            "0",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "stored scheduled start preview could not be built\n"
    assert not db_path.exists()
    for forbidden_fragment in (
        str(tmp_path),
        "missing-token",
        "secret",
        "auth",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_scheduled_start_preview_from_store_local_sanitizes_missing_course(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-preview-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--course-id",
            "missing-token-secret-auth-profile",
            "--class-time-index",
            "0",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "stored scheduled start preview could not be built\n"
    for forbidden_fragment in (
        str(tmp_path),
        "missing",
        "token",
        "secret",
        "auth",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_scheduled_start_preview_from_store_local_sanitizes_bad_index(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-preview-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--course-id",
            "cs101",
            "--class-time-index",
            "99",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "stored scheduled start preview could not be built\n"
    for forbidden_fragment in (
        str(tmp_path),
        "99",
        "out of range",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_scheduled_start_preview_from_store_local_sanitizes_malformed_store(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE courses (course_id TEXT PRIMARY KEY)")
        connection.execute("INSERT INTO courses (course_id) VALUES (?)", ("cs101",))

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-preview-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--course-id",
            "cs101",
            "--class-time-index",
            "0",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "stored scheduled start preview could not be built\n"
    for forbidden_fragment in (
        str(tmp_path),
        "class_times",
        "select",
        "sqlite",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_scheduled_start_preview_from_store_local_command_delegates_to_helpers(
    capsys,
    monkeypatch,
) -> None:
    received: dict[str, object] = {}
    schedule_store_module = "async_scholar.schedule_store"
    scheduled_start_module = "async_scholar.scheduled_start"
    fake_schedule_store_module = types.ModuleType(schedule_store_module)
    fake_scheduled_start_module = types.ModuleType(scheduled_start_module)
    fake_schedule_config = object()
    fake_stored_schedule = types.SimpleNamespace(schedule_config=fake_schedule_config)
    fake_plan = object()
    fake_clock = object()
    fake_preview = object()

    def fake_load(db_path: Path, course_id: str) -> object:
        received["db_path"] = db_path
        received["course_id"] = course_id
        return fake_stored_schedule

    def fake_build_plan(
        schedule_config: object,
        selected_class_time_index: int,
        source_kind: str,
        *,
        enabled: bool,
    ) -> object:
        received["schedule_config"] = schedule_config
        received["selected_class_time_index"] = selected_class_time_index
        received["source_kind"] = source_kind
        received["enabled"] = enabled
        return fake_plan

    class FakeClock:
        def __new__(cls, **kwargs: object) -> object:
            received["clock_kwargs"] = kwargs
            return fake_clock

    def fake_build_manual_result(
        plan: object,
        clock: object,
        session_id: str,
    ) -> object:
        received["manual_plan"] = plan
        received["manual_clock"] = clock
        received["session_id"] = session_id
        return fake_preview

    def fake_summary(preview: object) -> dict[str, object]:
        received["preview"] = preview
        return {
            "result_kind": "scheduled_start_manual_result",
            "status": "waiting",
            "session_id": "session-001",
            "course_id": "cs101",
            "source_kind": "file",
            "enabled": True,
            "clock_day_of_week": "monday",
            "clock_local_time": "08:30",
            "scheduled_day_of_week": "monday",
            "scheduled_local_start_time": "09:00",
            "due": False,
            "minutes_until_start": 30,
            "next_day_of_week": "monday",
            "next_local_start_time": "09:00",
        }

    fake_schedule_store_module.load_course_schedule_read_only = fake_load
    fake_scheduled_start_module.ScheduledStartClock = FakeClock
    fake_scheduled_start_module.build_scheduled_start_plan = fake_build_plan
    fake_scheduled_start_module.build_scheduled_start_manual_result = (
        fake_build_manual_result
    )
    fake_scheduled_start_module.scheduled_start_manual_result_safe_summary = (
        fake_summary
    )
    monkeypatch.setitem(sys.modules, schedule_store_module, fake_schedule_store_module)
    monkeypatch.setitem(
        sys.modules,
        scheduled_start_module,
        fake_scheduled_start_module,
    )

    exit_code = cli.main(
        [
            "scheduled-start-preview-from-store-local",
            "session-001",
            "--db-path",
            "schedule.sqlite",
            "--course-id",
            "cs101",
            "--class-time-index",
            "1",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "08:30",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out) == {
        "clock_day_of_week": "monday",
        "clock_local_time": "08:30",
        "course_id": "cs101",
        "due": False,
        "minutes_until_start": 30,
        "next_day_of_week": "monday",
        "next_local_start_time": "09:00",
        "scheduled_day_of_week": "monday",
        "scheduled_local_start_time": "09:00",
        "session_id": "session-001",
        "source_kind": "file",
        "status": "waiting",
    }
    assert captured.err == ""
    assert received == {
        "db_path": Path("schedule.sqlite"),
        "course_id": "cs101",
        "schedule_config": fake_schedule_config,
        "selected_class_time_index": 1,
        "source_kind": "file",
        "enabled": True,
        "clock_kwargs": {"day_of_week": "monday", "local_time": "08:30"},
        "manual_plan": fake_plan,
        "manual_clock": fake_clock,
        "session_id": "session-001",
        "preview": fake_preview,
    }


def test_scheduled_start_preview_from_store_local_handler_stays_read_only() -> None:
    source = inspect.getsource(
        cli._run_scheduled_start_preview_from_store_local_command
    )

    assert "load_course_schedule_read_only" in source
    assert "build_scheduled_start_plan" in source
    assert "ScheduledStartClock" in source
    assert "build_scheduled_start_manual_result" in source
    assert "scheduled_start_manual_result_safe_summary" in source
    for forbidden_fragment in (
        "load_course_schedule(",
        "save_course_schedule",
        "initialize_course_schedule_store",
        "_create_schema",
        "datetime",
        "now(",
        "sleep",
        "Timer(",
        "threading",
        "subprocess",
        "webbrowser",
        "requests",
        "httpx",
        "playwright",
        "sounddevice",
        "telegram",
        "desktop_notifier",
        "execute_archive",
        "archive_export",
        ".open(",
        ".read_text(",
        ".write_text(",
        ".mkdir(",
        ".unlink(",
        ".remove(",
        ".rmdir(",
    ):
        assert forbidden_fragment not in source


def test_scheduled_start_next_from_store_local_help_stays_lazy(monkeypatch) -> None:
    schedule_store_module = "async_scholar.schedule_store"
    scheduled_start_module = "async_scholar.scheduled_start"
    monkeypatch.delitem(sys.modules, schedule_store_module, raising=False)
    monkeypatch.delitem(sys.modules, scheduled_start_module, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-next-from-store-local",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar scheduled-start-next-from-store-local" in (
        result.stdout
    )
    assert "--db-path" in result.stdout
    assert "--clock-local-time" in result.stdout
    assert "non-executing" in result.stdout
    assert schedule_store_module not in sys.modules
    assert scheduled_start_module not in sys.modules


def test_scheduled_start_next_from_store_local_requires_explicit_metadata() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-next-from-store-local",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr == "stored next scheduled start preview could not be built\n"


def test_scheduled_start_next_from_store_local_sanitizes_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-next-from-store-local",
            "session-001",
            "C:\\Users\\student\\token-secret-auth-profile",
            "--db-path",
            "schedule.sqlite",
            "--course-id",
            "cs101",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "stored next scheduled start preview could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "unrecognized arguments",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_scheduled_start_next_from_store_local_sanitizes_misordered_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--db-path",
            "C:\\Users\\student\\token-secret-auth-profile",
            "scheduled-start-next-from-store-local",
            "session-001",
            "--course-id",
            "cs101",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "stored next scheduled start preview could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "invalid choice",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_scheduled_start_next_from_store_local_selects_first_upcoming_json(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-next-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--course-id",
            "cs101",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "08:30",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.count("\n") == 1
    assert json.loads(result.stdout) == {
        "clock_day_of_week": "monday",
        "clock_local_time": "08:30",
        "course_id": "cs101",
        "due": False,
        "minutes_until_start": 30,
        "next_day_of_week": "monday",
        "next_local_start_time": "09:00",
        "scheduled_day_of_week": "monday",
        "scheduled_local_start_time": "09:00",
        "selected_class_time_index": 0,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "waiting",
    }
    _assert_stored_schedule_next_preview_output_is_safe(
        result.stdout,
        result.stderr,
    )


def test_scheduled_start_next_from_store_local_selects_later_week_class(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-next-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--course-id",
            "cs101",
            "--source-kind",
            "mic",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "10:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["selected_class_time_index"] == 1
    assert payload["minutes_until_start"] == 3090
    assert payload["scheduled_day_of_week"] == "wednesday"
    assert payload["scheduled_local_start_time"] == "13:30"
    assert payload["source_kind"] == "mic"
    _assert_stored_schedule_next_preview_output_is_safe(
        result.stdout,
        result.stderr,
    )


def test_scheduled_start_next_from_store_local_disabled_does_not_select_json(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-next-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--course-id",
            "cs101",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
            "--disabled",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload == {
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_id": "cs101",
        "due": False,
        "minutes_until_start": None,
        "next_day_of_week": None,
        "next_local_start_time": None,
        "scheduled_day_of_week": None,
        "scheduled_local_start_time": None,
        "selected_class_time_index": None,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "disabled",
    }
    assert "enabled" not in payload
    assert "result_kind" not in payload
    _assert_stored_schedule_next_preview_output_is_safe(
        result.stdout,
        result.stderr,
    )


def test_scheduled_start_next_from_store_local_missing_db_does_not_create_file(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "missing-token-secret-auth-profile.sqlite"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-next-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--course-id",
            "cs101",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "stored next scheduled start preview could not be built\n"
    assert not db_path.exists()
    for forbidden_fragment in (
        str(tmp_path),
        "missing-token",
        "secret",
        "auth",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_scheduled_start_next_from_store_local_sanitizes_missing_course(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-next-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--course-id",
            "missing-token-secret-auth-profile",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "stored next scheduled start preview could not be built\n"
    for forbidden_fragment in (
        str(tmp_path),
        "missing",
        "token",
        "secret",
        "auth",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_scheduled_start_next_from_store_local_sanitizes_malformed_store(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE courses (course_id TEXT PRIMARY KEY)")
        connection.execute("INSERT INTO courses (course_id) VALUES (?)", ("cs101",))

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-next-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--course-id",
            "cs101",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "stored next scheduled start preview could not be built\n"
    for forbidden_fragment in (
        str(tmp_path),
        "class_times",
        "select",
        "sqlite",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_scheduled_start_next_from_store_local_command_delegates_to_helpers(
    capsys,
    monkeypatch,
) -> None:
    received: dict[str, object] = {}
    schedule_store_module = "async_scholar.schedule_store"
    scheduled_start_module = "async_scholar.scheduled_start"
    fake_schedule_store_module = types.ModuleType(schedule_store_module)
    fake_scheduled_start_module = types.ModuleType(scheduled_start_module)
    fake_schedule_config = object()
    fake_stored_schedule = types.SimpleNamespace(schedule_config=fake_schedule_config)
    fake_clock = object()

    def fake_load(db_path: Path, course_id: str) -> object:
        received["db_path"] = db_path
        received["course_id"] = course_id
        return fake_stored_schedule

    class FakeClock:
        def __new__(cls, **kwargs: object) -> object:
            received["clock_kwargs"] = kwargs
            return fake_clock

    def fake_build_next(
        schedule_config: object,
        clock: object,
        session_id: str,
        source_kind: str,
        *,
        enabled: bool,
    ) -> dict[str, object]:
        received["schedule_config"] = schedule_config
        received["clock"] = clock
        received["session_id"] = session_id
        received["source_kind"] = source_kind
        received["enabled"] = enabled
        return {
            "result_kind": "scheduled_start_manual_result",
            "status": "waiting",
            "session_id": "session-001",
            "course_id": "cs101",
            "source_kind": "file",
            "enabled": True,
            "clock_day_of_week": "monday",
            "clock_local_time": "08:30",
            "selected_class_time_index": 1,
            "scheduled_day_of_week": "monday",
            "scheduled_local_start_time": "09:00",
            "due": False,
            "minutes_until_start": 30,
            "next_day_of_week": "monday",
            "next_local_start_time": "09:00",
        }

    fake_schedule_store_module.load_course_schedule_read_only = fake_load
    fake_scheduled_start_module.ScheduledStartClock = FakeClock
    fake_scheduled_start_module.build_next_scheduled_start_preview_summary = (
        fake_build_next
    )
    monkeypatch.setitem(sys.modules, schedule_store_module, fake_schedule_store_module)
    monkeypatch.setitem(
        sys.modules,
        scheduled_start_module,
        fake_scheduled_start_module,
    )

    exit_code = cli.main(
        [
            "scheduled-start-next-from-store-local",
            "session-001",
            "--db-path",
            "schedule.sqlite",
            "--course-id",
            "cs101",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "08:30",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out) == {
        "clock_day_of_week": "monday",
        "clock_local_time": "08:30",
        "course_id": "cs101",
        "due": False,
        "minutes_until_start": 30,
        "next_day_of_week": "monday",
        "next_local_start_time": "09:00",
        "scheduled_day_of_week": "monday",
        "scheduled_local_start_time": "09:00",
        "selected_class_time_index": 1,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "waiting",
    }
    assert captured.err == ""
    assert received == {
        "db_path": Path("schedule.sqlite"),
        "course_id": "cs101",
        "clock_kwargs": {"day_of_week": "monday", "local_time": "08:30"},
        "schedule_config": fake_schedule_config,
        "clock": fake_clock,
        "session_id": "session-001",
        "source_kind": "file",
        "enabled": True,
    }


def test_scheduled_start_next_from_store_local_handler_stays_read_only() -> None:
    source = inspect.getsource(cli._run_scheduled_start_next_from_store_local_command)

    assert "load_course_schedule_read_only" in source
    assert "ScheduledStartClock" in source
    assert "build_next_scheduled_start_preview_summary" in source
    for forbidden_fragment in (
        "load_course_schedule(",
        "save_course_schedule",
        "initialize_course_schedule_store",
        "_create_schema",
        "datetime",
        "now(",
        "sleep",
        "Timer(",
        "threading",
        "subprocess",
        "webbrowser",
        "requests",
        "httpx",
        "playwright",
        "sounddevice",
        "telegram",
        "desktop_notifier",
        "execute_archive",
        "archive_export",
        ".open(",
        ".read_text(",
        ".write_text(",
        ".mkdir(",
        ".unlink(",
        ".remove(",
        ".rmdir(",
    ):
        assert forbidden_fragment not in source


def test_scheduled_start_due_list_from_store_local_help_stays_lazy(monkeypatch) -> None:
    schedule_store_module = "async_scholar.schedule_store"
    scheduled_start_module = "async_scholar.scheduled_start"
    monkeypatch.delitem(sys.modules, schedule_store_module, raising=False)
    monkeypatch.delitem(sys.modules, scheduled_start_module, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-due-list-from-store-local",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar scheduled-start-due-list-from-store-local" in (
        result.stdout
    )
    assert "--db-path" in result.stdout
    assert "--clock-local-time" in result.stdout
    assert "non-executing" in result.stdout
    assert schedule_store_module not in sys.modules
    assert scheduled_start_module not in sys.modules


def test_scheduled_start_due_list_from_store_local_requires_explicit_metadata() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-due-list-from-store-local",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr == "stored scheduled start due list could not be built\n"


def test_scheduled_start_due_list_from_store_local_sanitizes_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-due-list-from-store-local",
            "session-001",
            "C:\\Users\\student\\token-secret-auth-profile",
            "--db-path",
            "schedule.sqlite",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "stored scheduled start due list could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "unrecognized arguments",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_scheduled_start_due_list_from_store_local_sanitizes_misordered_failures() -> (
    None
):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--db-path",
            "C:\\Users\\student\\token-secret-auth-profile",
            "scheduled-start-due-list-from-store-local",
            "session-001",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "stored scheduled start due list could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "invalid choice",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_scheduled_start_due_list_from_store_local_rejects_bad_source_kind(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-due-list-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--source-kind",
            "browser",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "stored scheduled start due list could not be built\n"
    for forbidden_fragment in (
        "browser",
        "invalid choice",
        str(tmp_path),
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_scheduled_start_due_list_from_store_local_rejects_bad_clock(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-due-list-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "99:99",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "stored scheduled start due list could not be built\n"
    for forbidden_fragment in (
        "99:99",
        str(tmp_path),
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_scheduled_start_due_list_from_store_local_prints_safe_due_json(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)
    save_course_schedule(
        db_path,
        CourseMetadata(
            course_id="math101",
            title="Private Math",
            instructor_name="Dr. Secret",
            meeting_url="https://meet.example.edu/math?token=secret",
            meeting_label="Private math lecture",
        ),
        ScheduleConfig(
            course_id="math101",
            class_times=[
                {
                    "day_of_week": "monday",
                    "local_start_time": "09:00",
                    "duration_minutes": 60,
                    "timezone_name": "Asia/Manila",
                    "meeting_label": "Private math lecture",
                }
            ],
        ),
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-due-list-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.count("\n") == 1
    assert json.loads(result.stdout) == {
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 2,
        "courses": [
            {
                "course_id": "cs101",
                "due": True,
                "minutes_until_start": 0,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "selected_class_time_index": 0,
            },
            {
                "course_id": "math101",
                "due": True,
                "minutes_until_start": 0,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "selected_class_time_index": 0,
            },
        ],
        "due_count": 2,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "due",
    }
    _assert_stored_schedule_due_list_output_is_safe(result.stdout, result.stderr)


def test_scheduled_start_due_list_from_store_local_prints_empty_store_json(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    initialize_course_schedule_store(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-due-list-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--source-kind",
            "mic",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert json.loads(result.stdout) == {
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 0,
        "courses": [],
        "due_count": 0,
        "session_id": "session-001",
        "source_kind": "mic",
        "status": "waiting",
    }
    _assert_stored_schedule_due_list_output_is_safe(result.stdout, result.stderr)


def test_scheduled_start_due_list_from_store_local_disabled_has_no_due_courses(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-due-list-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
            "--disabled",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert json.loads(result.stdout) == {
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 1,
        "courses": [],
        "due_count": 0,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "disabled",
    }
    _assert_stored_schedule_due_list_output_is_safe(result.stdout, result.stderr)


def test_scheduled_start_due_list_from_store_local_missing_db_does_not_create_file(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "missing-token-secret-auth-profile.sqlite"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-due-list-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "stored scheduled start due list could not be built\n"
    assert not db_path.exists()
    for forbidden_fragment in (
        str(tmp_path),
        "missing-token",
        "secret",
        "auth",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_scheduled_start_due_list_from_store_local_sanitizes_malformed_store(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE courses (course_id TEXT PRIMARY KEY)")
        connection.execute("INSERT INTO courses (course_id) VALUES (?)", ("cs101",))

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-due-list-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "stored scheduled start due list could not be built\n"
    for forbidden_fragment in (
        str(tmp_path),
        "class_times",
        "select",
        "sqlite",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_scheduled_start_due_list_from_store_local_command_delegates_to_helpers(
    capsys,
    monkeypatch,
) -> None:
    received: dict[str, object] = {}
    schedule_store_module = "async_scholar.schedule_store"
    scheduled_start_module = "async_scholar.scheduled_start"
    fake_schedule_store_module = types.ModuleType(schedule_store_module)
    fake_scheduled_start_module = types.ModuleType(scheduled_start_module)
    fake_store_payload = object()
    fake_clock = object()

    def fake_list(db_path: Path) -> object:
        received["db_path"] = db_path
        return fake_store_payload

    class FakeClock:
        def __new__(cls, **kwargs: object) -> object:
            received["clock_kwargs"] = kwargs
            return fake_clock

    def fake_build_due_list(
        stored_courses: object,
        clock: object,
        session_id: str,
        source_kind: str,
        *,
        enabled: bool,
    ) -> dict[str, object]:
        received["stored_courses"] = stored_courses
        received["clock"] = clock
        received["session_id"] = session_id
        received["source_kind"] = source_kind
        received["enabled"] = enabled
        return {
            "status": "due",
            "session_id": "session-001",
            "source_kind": "file",
            "clock_day_of_week": "monday",
            "clock_local_time": "09:00",
            "course_count": 1,
            "due_count": 1,
            "courses": [
                {
                    "course_id": "cs101",
                    "selected_class_time_index": 0,
                    "scheduled_day_of_week": "monday",
                    "scheduled_local_start_time": "09:00",
                    "due": True,
                    "minutes_until_start": 0,
                    "meeting_url": "https://meet.example.edu/token-secret",
                }
            ],
            "private_title": "Confidential Systems",
        }

    fake_schedule_store_module.list_course_schedule_due_list_inputs = fake_list
    fake_scheduled_start_module.ScheduledStartClock = FakeClock
    fake_scheduled_start_module.build_scheduled_start_due_list_summary = (
        fake_build_due_list
    )
    monkeypatch.setitem(sys.modules, schedule_store_module, fake_schedule_store_module)
    monkeypatch.setitem(
        sys.modules,
        scheduled_start_module,
        fake_scheduled_start_module,
    )

    exit_code = cli.main(
        [
            "scheduled-start-due-list-from-store-local",
            "session-001",
            "--db-path",
            "schedule.sqlite",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out) == {
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 1,
        "courses": [
            {
                "course_id": "cs101",
                "due": True,
                "minutes_until_start": 0,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "selected_class_time_index": 0,
            }
        ],
        "due_count": 1,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "due",
    }
    assert captured.err == ""
    assert received == {
        "db_path": Path("schedule.sqlite"),
        "clock_kwargs": {"day_of_week": "monday", "local_time": "09:00"},
        "stored_courses": fake_store_payload,
        "clock": fake_clock,
        "session_id": "session-001",
        "source_kind": "file",
        "enabled": True,
    }
    _assert_stored_schedule_due_list_output_is_safe(captured.out, captured.err)


def test_scheduled_start_due_list_from_store_local_handler_stays_read_only() -> None:
    source = inspect.getsource(
        cli._run_scheduled_start_due_list_from_store_local_command
    )

    assert "list_course_schedule_due_list_inputs" in source
    assert "ScheduledStartClock" in source
    assert "build_scheduled_start_due_list_summary" in source
    for forbidden_fragment in (
        "load_course_schedule(",
        "load_course_schedule_read_only",
        "load_course_schedule_safe_summary",
        "list_course_schedule_safe_summaries",
        "save_course_schedule",
        "initialize_course_schedule_store",
        "_create_schema",
        "ScheduleConfig",
        "CourseMetadata",
        "datetime",
        "now(",
        "sleep",
        "Timer(",
        "threading",
        "asyncio",
        "subprocess",
        "webbrowser",
        "requests",
        "httpx",
        "playwright",
        "selenium",
        "sounddevice",
        "faster_whisper",
        "mic_recording",
        "telegram",
        "desktop_notifier",
        "execute_archive",
        "archive_export",
        "archive_delete",
        ".open(",
        ".read_text(",
        ".write_text(",
        ".mkdir(",
        ".unlink(",
        ".remove(",
        ".rmdir(",
        "rmtree",
    ):
        assert forbidden_fragment not in source


def test_session_stop_preview_from_store_local_help_stays_lazy(monkeypatch) -> None:
    schedule_store_module = "async_scholar.schedule_store"
    session_stop_module = "async_scholar.session_stop"
    monkeypatch.delitem(sys.modules, schedule_store_module, raising=False)
    monkeypatch.delitem(sys.modules, session_stop_module, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-stop-preview-from-store-local",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar session-stop-preview-from-store-local" in (
        result.stdout
    )
    assert "--db-path" in result.stdout
    assert "--class-time-index" in result.stdout
    assert "--source-kind" in result.stdout
    assert "non-executing" in result.stdout
    assert schedule_store_module not in sys.modules
    assert session_stop_module not in sys.modules


def test_session_window_plan_from_store_local_help_stays_lazy(monkeypatch) -> None:
    schedule_store_module = "async_scholar.schedule_store"
    scheduled_start_module = "async_scholar.scheduled_start"
    session_window_module = "async_scholar.session_window"
    monkeypatch.delitem(sys.modules, schedule_store_module, raising=False)
    monkeypatch.delitem(sys.modules, scheduled_start_module, raising=False)
    monkeypatch.delitem(sys.modules, session_window_module, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-plan-from-store-local",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar session-window-plan-from-store-local" in (
        result.stdout
    )
    assert "--db-path" in result.stdout
    assert "--clock-local-time" in result.stdout
    assert "non-executing" in result.stdout
    assert schedule_store_module not in sys.modules
    assert scheduled_start_module not in sys.modules
    assert session_window_module not in sys.modules


def test_session_window_plan_from_store_local_requires_explicit_metadata() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-plan-from-store-local",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr == "stored session window plan could not be built\n"


def test_session_window_plan_from_store_local_prints_safe_due_json(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)
    save_course_schedule(
        db_path,
        CourseMetadata(
            course_id="math101",
            title="Private Math",
            instructor_name="Dr. Secret",
            meeting_url="https://meet.example.edu/math?token=secret",
            meeting_label="Private math lecture",
        ),
        ScheduleConfig(
            course_id="math101",
            class_times=[
                {
                    "day_of_week": "monday",
                    "local_start_time": "09:00",
                    "duration_minutes": 60,
                    "timezone_name": "Asia/Manila",
                    "meeting_label": "Private math lecture",
                }
            ],
        ),
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-plan-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.count("\n") == 1
    assert json.loads(result.stdout) == {
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 2,
        "courses": [
            {
                "course_id": "cs101",
                "due": True,
                "enabled": True,
                "minutes_until_start": 0,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "selected_class_time_index": 0,
                "stop_after_minutes": 75,
            },
            {
                "course_id": "math101",
                "due": True,
                "enabled": True,
                "minutes_until_start": 0,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "selected_class_time_index": 0,
                "stop_after_minutes": 60,
            },
        ],
        "due_count": 2,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "due",
    }
    _assert_session_window_plan_output_is_safe(result.stdout, result.stderr)


def test_session_window_plan_from_store_local_disabled_and_empty_due(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)

    disabled = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-plan-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--source-kind",
            "mic",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
            "--disabled",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    waiting = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-plan-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "tuesday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert disabled.returncode == 0
    assert json.loads(disabled.stdout) == {
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 1,
        "courses": [],
        "due_count": 0,
        "session_id": "session-001",
        "source_kind": "mic",
        "status": "disabled",
    }
    assert waiting.returncode == 0
    assert json.loads(waiting.stdout)["status"] == "waiting"
    assert json.loads(waiting.stdout)["courses"] == []
    _assert_session_window_plan_output_is_safe(disabled.stdout, disabled.stderr)
    _assert_session_window_plan_output_is_safe(waiting.stdout, waiting.stderr)


def test_session_window_plan_from_store_local_sanitizes_failures(
    tmp_path: Path,
) -> None:
    missing_db_path = tmp_path / "missing-token-secret-auth-profile.sqlite"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-plan-from-store-local",
            "session-001",
            "--db-path",
            str(missing_db_path),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "stored session window plan could not be built\n"
    assert not missing_db_path.exists()
    for forbidden_fragment in (
        str(tmp_path),
        "missing-token",
        "secret",
        "auth",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_window_plan_from_store_local_rejects_bad_clock_and_source(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)

    bad_source = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-plan-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--source-kind",
            "browser",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    bad_clock = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-plan-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "99:99",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert bad_source.returncode == 2
    assert bad_source.stdout == ""
    assert bad_source.stderr == "stored session window plan could not be built\n"
    assert bad_clock.returncode == 1
    assert bad_clock.stdout == ""
    assert bad_clock.stderr == "stored session window plan could not be built\n"


def test_session_window_plan_from_store_local_command_delegates_to_helpers(
    capsys,
    monkeypatch,
) -> None:
    received: dict[str, object] = {}
    schedule_store_module = "async_scholar.schedule_store"
    scheduled_start_module = "async_scholar.scheduled_start"
    session_window_module = "async_scholar.session_window"
    fake_schedule_store_module = types.ModuleType(schedule_store_module)
    fake_scheduled_start_module = types.ModuleType(scheduled_start_module)
    fake_session_window_module = types.ModuleType(session_window_module)
    fake_store_payload = object()
    fake_clock = object()

    def fake_list(db_path: Path) -> object:
        received["db_path"] = db_path
        return fake_store_payload

    class FakeClock:
        def __new__(cls, **kwargs: object) -> object:
            received["clock_kwargs"] = kwargs
            return fake_clock

    def fake_build(
        stored_courses: object,
        clock: object,
        session_id: str,
        source_kind: str,
        *,
        enabled: bool,
    ) -> dict[str, object]:
        received["stored_courses"] = stored_courses
        received["clock"] = clock
        received["session_id"] = session_id
        received["source_kind"] = source_kind
        received["enabled"] = enabled
        return {
            "status": "due",
            "session_id": "session-001",
            "source_kind": "file",
            "clock_day_of_week": "monday",
            "clock_local_time": "09:00",
            "course_count": 1,
            "due_count": 1,
            "courses": [
                {
                    "course_id": "cs101",
                    "selected_class_time_index": 0,
                    "scheduled_day_of_week": "monday",
                    "scheduled_local_start_time": "09:00",
                    "due": True,
                    "minutes_until_start": 0,
                    "stop_after_minutes": 75,
                    "enabled": True,
                    "meeting_url": "https://meet.example.edu/token-secret",
                }
            ],
            "private_title": "Confidential Systems",
        }

    fake_schedule_store_module.list_course_schedule_session_window_inputs = fake_list
    fake_scheduled_start_module.ScheduledStartClock = FakeClock
    fake_session_window_module.build_stored_session_window_plan_summary = fake_build
    monkeypatch.setitem(sys.modules, schedule_store_module, fake_schedule_store_module)
    monkeypatch.setitem(
        sys.modules,
        scheduled_start_module,
        fake_scheduled_start_module,
    )
    monkeypatch.setitem(sys.modules, session_window_module, fake_session_window_module)

    exit_code = cli.main(
        [
            "session-window-plan-from-store-local",
            "session-001",
            "--db-path",
            "schedule.sqlite",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out) == {
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 1,
        "courses": [
            {
                "course_id": "cs101",
                "due": True,
                "enabled": True,
                "minutes_until_start": 0,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "selected_class_time_index": 0,
                "stop_after_minutes": 75,
            }
        ],
        "due_count": 1,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "due",
    }
    assert captured.err == ""
    assert received == {
        "db_path": Path("schedule.sqlite"),
        "clock_kwargs": {"day_of_week": "monday", "local_time": "09:00"},
        "stored_courses": fake_store_payload,
        "clock": fake_clock,
        "session_id": "session-001",
        "source_kind": "file",
        "enabled": True,
    }
    _assert_session_window_plan_output_is_safe(captured.out, captured.err)


def test_session_window_plan_from_store_local_handler_stays_read_only() -> None:
    source = inspect.getsource(cli._run_session_window_plan_from_store_local_command)

    assert "list_course_schedule_session_window_inputs" in source
    assert "ScheduledStartClock" in source
    assert "build_stored_session_window_plan_summary" in source
    for forbidden_fragment in (
        "load_course_schedule(",
        "load_course_schedule_read_only",
        "load_course_schedule_safe_summary",
        "list_course_schedule_safe_summaries",
        "list_course_schedule_due_list_inputs",
        "load_course_schedule_session_stop_input",
        "save_course_schedule",
        "initialize_course_schedule_store",
        "_create_schema",
        "ScheduleConfig",
        "CourseMetadata",
        "datetime",
        "now(",
        "sleep",
        "Timer(",
        "threading",
        "asyncio",
        "subprocess",
        "webbrowser",
        "requests",
        "httpx",
        "playwright",
        "selenium",
        "sounddevice",
        "faster_whisper",
        "mic_recording",
        "telegram",
        "desktop_notifier",
        "execute_archive",
        "archive_export",
        "archive_delete",
        ".open(",
        ".read_text(",
        ".write_text(",
        ".mkdir(",
        ".unlink(",
        ".remove(",
        ".rmdir(",
        "rmtree",
    ):
        assert forbidden_fragment not in source


def test_session_window_archive_preflight_from_store_local_help_stays_lazy(
    monkeypatch,
) -> None:
    schedule_store_module = "async_scholar.schedule_store"
    scheduled_start_module = "async_scholar.scheduled_start"
    preflight_module = "async_scholar.session_window_archive_preflight"
    monkeypatch.delitem(sys.modules, schedule_store_module, raising=False)
    monkeypatch.delitem(sys.modules, scheduled_start_module, raising=False)
    monkeypatch.delitem(sys.modules, preflight_module, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-archive-preflight-from-store-local",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar session-window-archive-preflight-from-store-local" in (
        result.stdout
    )
    assert "--db-path" in result.stdout
    assert "--archive-root" in result.stdout
    assert "--clock-local-time" in result.stdout
    assert "read-only" in result.stdout
    assert schedule_store_module not in sys.modules
    assert scheduled_start_module not in sys.modules
    assert preflight_module not in sys.modules


def test_session_window_archive_preflight_from_store_local_requires_metadata() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-archive-preflight-from-store-local",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert (
        result.stderr == "stored session window archive preflight could not be built\n"
    )


def test_session_window_archive_preflight_from_store_local_prints_safe_json(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    archive_root = tmp_path / "archive"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    _write_private_course_schedule(db_path)
    (session_dir / "events.jsonl").write_text(
        "private event token secret auth profile payload",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-archive-preflight-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.count("\n") == 1
    assert json.loads(result.stdout) == {
        "archive_existing_count": 1,
        "archive_missing_count": 6,
        "archive_recovery_status": "partial",
        "archive_total_existing_size_bytes": len(
            b"private event token secret auth profile payload"
        ),
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 1,
        "courses": [
            {
                "course_id": "cs101",
                "due": True,
                "enabled": True,
                "minutes_until_start": 0,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "selected_class_time_index": 0,
                "stop_after_minutes": 75,
            }
        ],
        "due_count": 1,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "due",
    }
    _assert_session_window_archive_preflight_output_is_safe(
        result.stdout,
        result.stderr,
    )


def test_session_window_archive_preflight_from_store_local_disabled(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    archive_root = tmp_path / "archive"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-archive-preflight-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "mic",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
            "--disabled",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout) == {
        "archive_existing_count": 0,
        "archive_missing_count": 7,
        "archive_recovery_status": "empty",
        "archive_total_existing_size_bytes": 0,
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 1,
        "courses": [],
        "due_count": 0,
        "session_id": "session-001",
        "source_kind": "mic",
        "status": "disabled",
    }
    _assert_session_window_archive_preflight_output_is_safe(
        result.stdout,
        result.stderr,
    )


def test_session_window_archive_preflight_from_store_local_sanitizes_db_failure(
    tmp_path: Path,
) -> None:
    missing_db_path = tmp_path / "missing-token-secret-auth-profile.sqlite"
    archive_root = tmp_path / "archive"
    (archive_root / "session-001").mkdir(parents=True)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-archive-preflight-from-store-local",
            "session-001",
            "--db-path",
            str(missing_db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert (
        result.stderr == "stored session window archive preflight could not be built\n"
    )
    assert not missing_db_path.exists()
    for forbidden_fragment in (
        str(tmp_path),
        "missing-token",
        "secret",
        "auth",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_window_archive_preflight_from_store_local_sanitizes_malformed_db(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    archive_root = tmp_path / "archive"
    (archive_root / "session-001").mkdir(parents=True)
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE courses (course_id TEXT PRIMARY KEY)")
        connection.execute("INSERT INTO courses (course_id) VALUES (?)", ("cs101",))

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-archive-preflight-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert (
        result.stderr == "stored session window archive preflight could not be built\n"
    )
    for forbidden_fragment in (
        str(tmp_path),
        "class_times",
        "select",
        "sqlite",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_window_archive_preflight_from_store_local_sanitizes_archive_failure(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    archive_root = tmp_path / "archive-token-secret-auth-profile"
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-archive-preflight-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert (
        result.stderr == "stored session window archive preflight could not be built\n"
    )
    assert not archive_root.exists()
    for forbidden_fragment in (
        str(tmp_path),
        "archive-token",
        "secret",
        "auth",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_window_archive_preflight_from_store_local_rejects_source() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-archive-preflight-from-store-local",
            "session-001",
            "--db-path",
            "schedule.sqlite",
            "--archive-root",
            "archive",
            "--source-kind",
            "browser",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert (
        result.stderr == "stored session window archive preflight could not be built\n"
    )


def test_session_window_archive_preflight_command_delegates_to_helpers(
    capsys,
    monkeypatch,
) -> None:
    received: dict[str, object] = {}
    schedule_store_module = "async_scholar.schedule_store"
    scheduled_start_module = "async_scholar.scheduled_start"
    preflight_module = "async_scholar.session_window_archive_preflight"
    fake_schedule_store_module = types.ModuleType(schedule_store_module)
    fake_scheduled_start_module = types.ModuleType(scheduled_start_module)
    fake_preflight_module = types.ModuleType(preflight_module)
    fake_store_payload = object()
    fake_clock = object()

    def fake_list(db_path: Path) -> object:
        received["db_path"] = db_path
        return fake_store_payload

    class FakeClock:
        def __new__(cls, **kwargs: object) -> object:
            received["clock_kwargs"] = kwargs
            return fake_clock

    def fake_build(
        stored_courses: object,
        archive_root: Path,
        session_id: str,
        source_kind: str,
        clock: object,
        *,
        enabled: bool,
    ) -> dict[str, object]:
        received["stored_courses"] = stored_courses
        received["archive_root"] = archive_root
        received["session_id"] = session_id
        received["source_kind"] = source_kind
        received["clock"] = clock
        received["enabled"] = enabled
        return {
            "status": "due",
            "session_id": "session-001",
            "source_kind": "file",
            "clock_day_of_week": "monday",
            "clock_local_time": "09:00",
            "course_count": 1,
            "due_count": 1,
            "archive_recovery_status": "partial",
            "archive_existing_count": 1,
            "archive_missing_count": 6,
            "archive_total_existing_size_bytes": 2,
            "artifacts": [{"filename": "events.jsonl", "size_bytes": 2}],
            "courses": [
                {
                    "course_id": "cs101",
                    "selected_class_time_index": 0,
                    "scheduled_day_of_week": "monday",
                    "scheduled_local_start_time": "09:00",
                    "due": True,
                    "minutes_until_start": 0,
                    "stop_after_minutes": 75,
                    "enabled": True,
                    "meeting_url": "https://meet.example.edu/token-secret",
                }
            ],
        }

    fake_schedule_store_module.list_course_schedule_session_window_inputs = fake_list
    fake_scheduled_start_module.ScheduledStartClock = FakeClock
    fake_preflight_module.build_session_window_archive_preflight_summary = fake_build
    monkeypatch.setitem(sys.modules, schedule_store_module, fake_schedule_store_module)
    monkeypatch.setitem(
        sys.modules,
        scheduled_start_module,
        fake_scheduled_start_module,
    )
    monkeypatch.setitem(sys.modules, preflight_module, fake_preflight_module)

    exit_code = cli.main(
        [
            "session-window-archive-preflight-from-store-local",
            "session-001",
            "--db-path",
            "schedule.sqlite",
            "--archive-root",
            "archive-root",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out) == {
        "archive_existing_count": 1,
        "archive_missing_count": 6,
        "archive_recovery_status": "partial",
        "archive_total_existing_size_bytes": 2,
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 1,
        "courses": [
            {
                "course_id": "cs101",
                "due": True,
                "enabled": True,
                "minutes_until_start": 0,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "selected_class_time_index": 0,
                "stop_after_minutes": 75,
            }
        ],
        "due_count": 1,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "due",
    }
    assert captured.err == ""
    assert received == {
        "db_path": Path("schedule.sqlite"),
        "clock_kwargs": {"day_of_week": "monday", "local_time": "09:00"},
        "stored_courses": fake_store_payload,
        "archive_root": Path("archive-root"),
        "session_id": "session-001",
        "source_kind": "file",
        "clock": fake_clock,
        "enabled": True,
    }
    _assert_session_window_archive_preflight_output_is_safe(
        captured.out,
        captured.err,
    )


def test_session_window_archive_preflight_handler_stays_read_only() -> None:
    source = inspect.getsource(
        cli._run_session_window_archive_preflight_from_store_local_command
    )

    assert "list_course_schedule_session_window_inputs" in source
    assert "ScheduledStartClock" in source
    assert "build_session_window_archive_preflight_summary" in source
    for forbidden_fragment in (
        "load_course_schedule(",
        "load_course_schedule_read_only",
        "load_course_schedule_safe_summary",
        "list_course_schedule_safe_summaries",
        "list_course_schedule_due_list_inputs",
        "load_course_schedule_session_stop_input",
        "save_course_schedule",
        "initialize_course_schedule_store",
        "_create_schema",
        "ScheduleConfig",
        "CourseMetadata",
        "datetime",
        "now(",
        "sleep",
        "Timer(",
        "threading",
        "asyncio",
        "subprocess",
        "webbrowser",
        "requests",
        "httpx",
        "playwright",
        "selenium",
        "sounddevice",
        "faster_whisper",
        "mic_recording",
        "telegram",
        "desktop_notifier",
        "execute_archive",
        "archive_delete",
        ".open(",
        ".read_text(",
        ".write_text(",
        ".mkdir(",
        ".unlink(",
        ".remove(",
        ".rmdir(",
        "rmtree",
    ):
        assert forbidden_fragment not in source


def test_session_window_alert_preview_from_store_local_help_stays_lazy(
    monkeypatch,
) -> None:
    schedule_store_module = "async_scholar.schedule_store"
    scheduled_start_module = "async_scholar.scheduled_start"
    alert_preview_module = "async_scholar.session_window_alert_preview"
    monkeypatch.delitem(sys.modules, schedule_store_module, raising=False)
    monkeypatch.delitem(sys.modules, scheduled_start_module, raising=False)
    monkeypatch.delitem(sys.modules, alert_preview_module, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-alert-preview-from-store-local",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar session-window-alert-preview-from-store-local" in (
        result.stdout
    )
    assert "--db-path" in result.stdout
    assert "--clock-local-time" in result.stdout
    assert "metadata-only" in result.stdout
    assert schedule_store_module not in sys.modules
    assert scheduled_start_module not in sys.modules
    assert alert_preview_module not in sys.modules


def test_session_window_alert_preview_from_store_local_requires_metadata() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-alert-preview-from-store-local",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr == "stored session window alert preview could not be built\n"


def test_session_window_alert_preview_from_store_local_prints_safe_json(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)
    save_course_schedule(
        db_path,
        CourseMetadata(
            course_id="math101",
            title="Private Math",
            instructor_name="Dr. Secret",
            meeting_url="https://meet.example.edu/math?token=secret",
            meeting_label="Private math lecture",
        ),
        ScheduleConfig(
            course_id="math101",
            class_times=[
                {
                    "day_of_week": "monday",
                    "local_start_time": "09:00",
                    "duration_minutes": 60,
                    "timezone_name": "Asia/Manila",
                    "meeting_label": "Private math lecture",
                }
            ],
        ),
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-alert-preview-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.count("\n") == 1
    assert json.loads(result.stdout) == {
        "alert_preview_count": 2,
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 2,
        "courses": [
            {
                "alert_preview": {
                    "alert_kind": "participation_check",
                    "delivery": "none",
                    "requires_confirmation": True,
                },
                "course_id": "cs101",
                "due": True,
                "enabled": True,
                "minutes_until_start": 0,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "selected_class_time_index": 0,
                "stop_after_minutes": 75,
            },
            {
                "alert_preview": {
                    "alert_kind": "participation_check",
                    "delivery": "none",
                    "requires_confirmation": True,
                },
                "course_id": "math101",
                "due": True,
                "enabled": True,
                "minutes_until_start": 0,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "selected_class_time_index": 0,
                "stop_after_minutes": 60,
            },
        ],
        "due_count": 2,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "due",
    }
    _assert_session_window_alert_preview_output_is_safe(result.stdout, result.stderr)


def test_session_window_alert_preview_from_store_local_disabled_and_empty_due(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)

    disabled = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-alert-preview-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--source-kind",
            "mic",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
            "--disabled",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    waiting = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-alert-preview-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "tuesday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert disabled.returncode == 0
    assert json.loads(disabled.stdout) == {
        "alert_preview_count": 0,
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 1,
        "courses": [],
        "due_count": 0,
        "session_id": "session-001",
        "source_kind": "mic",
        "status": "disabled",
    }
    assert waiting.returncode == 0
    assert json.loads(waiting.stdout)["alert_preview_count"] == 0
    assert json.loads(waiting.stdout)["status"] == "waiting"
    assert json.loads(waiting.stdout)["courses"] == []
    _assert_session_window_alert_preview_output_is_safe(
        disabled.stdout,
        disabled.stderr,
    )
    _assert_session_window_alert_preview_output_is_safe(
        waiting.stdout,
        waiting.stderr,
    )


def test_session_window_alert_preview_from_store_local_sanitizes_failures(
    tmp_path: Path,
) -> None:
    missing_db_path = tmp_path / "missing-token-secret-auth-profile.sqlite"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-alert-preview-from-store-local",
            "session-001",
            "--db-path",
            str(missing_db_path),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "stored session window alert preview could not be built\n"
    assert not missing_db_path.exists()
    for forbidden_fragment in (
        str(tmp_path),
        "missing-token",
        "secret",
        "auth",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_window_alert_preview_from_store_local_sanitizes_malformed_db(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE courses (course_id TEXT PRIMARY KEY)")
        connection.execute("INSERT INTO courses (course_id) VALUES (?)", ("cs101",))

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-alert-preview-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "stored session window alert preview could not be built\n"
    for forbidden_fragment in (
        str(tmp_path),
        "class_times",
        "select",
        "sqlite",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_window_alert_preview_from_store_local_rejects_bad_source_and_clock(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)

    bad_source = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-alert-preview-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--source-kind",
            "browser",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    bad_clock = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-alert-preview-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "99:99",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert bad_source.returncode == 2
    assert bad_source.stdout == ""
    assert (
        bad_source.stderr == "stored session window alert preview could not be built\n"
    )
    assert bad_clock.returncode == 1
    assert bad_clock.stdout == ""
    assert (
        bad_clock.stderr == "stored session window alert preview could not be built\n"
    )


def test_session_window_alert_preview_command_delegates_to_helpers(
    capsys,
    monkeypatch,
) -> None:
    received: dict[str, object] = {}
    schedule_store_module = "async_scholar.schedule_store"
    scheduled_start_module = "async_scholar.scheduled_start"
    alert_preview_module = "async_scholar.session_window_alert_preview"
    fake_schedule_store_module = types.ModuleType(schedule_store_module)
    fake_scheduled_start_module = types.ModuleType(scheduled_start_module)
    fake_alert_preview_module = types.ModuleType(alert_preview_module)
    fake_store_payload = object()
    fake_clock = object()

    def fake_list(db_path: Path) -> object:
        received["db_path"] = db_path
        return fake_store_payload

    class FakeClock:
        def __new__(cls, **kwargs: object) -> object:
            received["clock_kwargs"] = kwargs
            return fake_clock

    def fake_build(
        stored_courses: object,
        session_id: str,
        source_kind: str,
        clock: object,
        *,
        enabled: bool,
    ) -> dict[str, object]:
        received["stored_courses"] = stored_courses
        received["session_id"] = session_id
        received["source_kind"] = source_kind
        received["clock"] = clock
        received["enabled"] = enabled
        return {
            "status": "due",
            "session_id": "session-001",
            "source_kind": "file",
            "clock_day_of_week": "monday",
            "clock_local_time": "09:00",
            "course_count": 1,
            "due_count": 1,
            "alert_preview_count": 1,
            "courses": [
                {
                    "course_id": "cs101",
                    "selected_class_time_index": 0,
                    "scheduled_day_of_week": "monday",
                    "scheduled_local_start_time": "09:00",
                    "due": True,
                    "minutes_until_start": 0,
                    "stop_after_minutes": 75,
                    "enabled": True,
                    "meeting_url": "https://meet.example.edu/token-secret",
                    "alert_preview": {
                        "alert_kind": "participation_check",
                        "delivery": "none",
                        "requires_confirmation": True,
                        "target": "private-device-token",
                    },
                }
            ],
            "private_title": "Confidential Systems",
        }

    fake_schedule_store_module.list_course_schedule_session_window_inputs = fake_list
    fake_scheduled_start_module.ScheduledStartClock = FakeClock
    fake_alert_preview_module.build_session_window_alert_preview_summary = fake_build
    monkeypatch.setitem(sys.modules, schedule_store_module, fake_schedule_store_module)
    monkeypatch.setitem(
        sys.modules,
        scheduled_start_module,
        fake_scheduled_start_module,
    )
    monkeypatch.setitem(sys.modules, alert_preview_module, fake_alert_preview_module)

    exit_code = cli.main(
        [
            "session-window-alert-preview-from-store-local",
            "session-001",
            "--db-path",
            "schedule.sqlite",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out) == {
        "alert_preview_count": 1,
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 1,
        "courses": [
            {
                "alert_preview": {
                    "alert_kind": "participation_check",
                    "delivery": "none",
                    "requires_confirmation": True,
                },
                "course_id": "cs101",
                "due": True,
                "enabled": True,
                "minutes_until_start": 0,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "selected_class_time_index": 0,
                "stop_after_minutes": 75,
            }
        ],
        "due_count": 1,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "due",
    }
    assert captured.err == ""
    assert received == {
        "db_path": Path("schedule.sqlite"),
        "clock_kwargs": {"day_of_week": "monday", "local_time": "09:00"},
        "stored_courses": fake_store_payload,
        "session_id": "session-001",
        "source_kind": "file",
        "clock": fake_clock,
        "enabled": True,
    }
    _assert_session_window_alert_preview_output_is_safe(captured.out, captured.err)


def test_session_window_alert_preview_cli_safe_summary_requires_fixed_metadata() -> (
    None
):
    with pytest.raises(ValueError) as exc_info:
        cli._stored_session_window_alert_preview_safe_summary(
            {
                "status": "due",
                "session_id": "session-001",
                "source_kind": "file",
                "clock_day_of_week": "monday",
                "clock_local_time": "09:00",
                "course_count": 1,
                "due_count": 1,
                "alert_preview_count": 1,
                "courses": [
                    {
                        "course_id": "cs101",
                        "selected_class_time_index": 0,
                        "scheduled_day_of_week": "monday",
                        "scheduled_local_start_time": "09:00",
                        "due": True,
                        "minutes_until_start": 0,
                        "stop_after_minutes": 75,
                        "enabled": True,
                        "alert_preview": {
                            "alert_kind": "private-token",
                            "delivery": "none",
                            "requires_confirmation": True,
                        },
                    }
                ],
            }
        )

    assert (
        str(exc_info.value) == "stored session window alert preview could not be built"
    )


def test_session_window_alert_preview_handler_stays_read_only() -> None:
    source = inspect.getsource(
        cli._run_session_window_alert_preview_from_store_local_command
    )

    assert "list_course_schedule_session_window_inputs" in source
    assert "ScheduledStartClock" in source
    assert "build_session_window_alert_preview_summary" in source
    for forbidden_fragment in (
        "load_course_schedule(",
        "load_course_schedule_read_only",
        "load_course_schedule_safe_summary",
        "list_course_schedule_safe_summaries",
        "list_course_schedule_due_list_inputs",
        "load_course_schedule_session_stop_input",
        "save_course_schedule",
        "initialize_course_schedule_store",
        "_create_schema",
        "ScheduleConfig",
        "CourseMetadata",
        "datetime",
        "now(",
        "sleep",
        "Timer(",
        "threading",
        "asyncio",
        "subprocess",
        "webbrowser",
        "requests",
        "httpx",
        "playwright",
        "selenium",
        "sounddevice",
        "faster_whisper",
        "mic_recording",
        "telegram",
        "desktop_notifier",
        "execute_archive",
        "archive_export",
        "archive_delete",
        ".open(",
        ".read_text(",
        ".write_text(",
        ".mkdir(",
        ".unlink(",
        ".remove(",
        ".rmdir(",
        "rmtree",
    ):
        assert forbidden_fragment not in source


def test_session_window_readiness_preflight_from_store_local_help_stays_lazy(
    monkeypatch,
) -> None:
    schedule_store_module = "async_scholar.schedule_store"
    scheduled_start_module = "async_scholar.scheduled_start"
    preflight_module = "async_scholar.session_window_readiness_preflight"
    monkeypatch.delitem(sys.modules, schedule_store_module, raising=False)
    monkeypatch.delitem(sys.modules, scheduled_start_module, raising=False)
    monkeypatch.delitem(sys.modules, preflight_module, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-readiness-preflight-from-store-local",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert (
        "usage: async_scholar session-window-readiness-preflight-from-store-local"
        in result.stdout
    )
    assert "--db-path" in result.stdout
    assert "--archive-root" in result.stdout
    assert "--clock-local-time" in result.stdout
    assert "read-only" in result.stdout
    assert schedule_store_module not in sys.modules
    assert scheduled_start_module not in sys.modules
    assert preflight_module not in sys.modules


def test_session_window_readiness_preflight_from_store_local_requires_metadata() -> (
    None
):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-readiness-preflight-from-store-local",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert (
        result.stderr
        == "stored session window readiness preflight could not be built\n"
    )


def test_session_window_readiness_preflight_from_store_local_prints_safe_json(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    archive_root = tmp_path / "archive"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    _write_private_course_schedule(db_path)
    (session_dir / "events.jsonl").write_text(
        "private event token secret auth profile payload",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-readiness-preflight-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.count("\n") == 1
    assert json.loads(result.stdout) == {
        "alert_preview_count": 1,
        "archive_existing_count": 1,
        "archive_missing_count": 6,
        "archive_recovery_status": "partial",
        "archive_total_existing_size_bytes": len(
            b"private event token secret auth profile payload"
        ),
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 1,
        "courses": [
            {
                "alert_preview": {
                    "alert_kind": "participation_check",
                    "delivery": "none",
                    "requires_confirmation": True,
                },
                "course_id": "cs101",
                "due": True,
                "enabled": True,
                "minutes_until_start": 0,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "selected_class_time_index": 0,
                "stop_after_minutes": 75,
            }
        ],
        "due_count": 1,
        "ready_to_start": True,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "due",
    }
    _assert_session_window_readiness_preflight_output_is_safe(
        result.stdout,
        result.stderr,
    )


def test_session_window_readiness_preflight_from_store_local_disabled(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    archive_root = tmp_path / "archive"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-readiness-preflight-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "mic",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
            "--disabled",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout) == {
        "alert_preview_count": 0,
        "archive_existing_count": 0,
        "archive_missing_count": 7,
        "archive_recovery_status": "empty",
        "archive_total_existing_size_bytes": 0,
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 1,
        "courses": [],
        "due_count": 0,
        "ready_to_start": False,
        "session_id": "session-001",
        "source_kind": "mic",
        "status": "disabled",
    }
    _assert_session_window_readiness_preflight_output_is_safe(
        result.stdout,
        result.stderr,
    )


def test_session_window_readiness_preflight_from_store_local_sanitizes_db_failure(
    tmp_path: Path,
) -> None:
    missing_db_path = tmp_path / "missing-token-secret-auth-profile.sqlite"
    archive_root = tmp_path / "archive"
    (archive_root / "session-001").mkdir(parents=True)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-readiness-preflight-from-store-local",
            "session-001",
            "--db-path",
            str(missing_db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert (
        result.stderr
        == "stored session window readiness preflight could not be built\n"
    )
    assert not missing_db_path.exists()
    for forbidden_fragment in (
        str(tmp_path),
        "missing-token",
        "secret",
        "auth",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_window_readiness_preflight_from_store_local_sanitizes_malformed_db(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    archive_root = tmp_path / "archive"
    (archive_root / "session-001").mkdir(parents=True)
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE courses (course_id TEXT PRIMARY KEY)")
        connection.execute("INSERT INTO courses (course_id) VALUES (?)", ("cs101",))

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-readiness-preflight-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert (
        result.stderr
        == "stored session window readiness preflight could not be built\n"
    )
    for forbidden_fragment in (
        str(tmp_path),
        "class_times",
        "select",
        "sqlite",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_window_readiness_preflight_from_store_local_sanitizes_archive_failure(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    archive_root = tmp_path / "archive-token-secret-auth-profile"
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-readiness-preflight-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert (
        result.stderr
        == "stored session window readiness preflight could not be built\n"
    )
    assert not archive_root.exists()
    for forbidden_fragment in (
        str(tmp_path),
        "archive-token",
        "secret",
        "auth",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_window_readiness_preflight_from_store_local_rejects_source() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-readiness-preflight-from-store-local",
            "session-001",
            "--db-path",
            "schedule.sqlite",
            "--archive-root",
            "archive",
            "--source-kind",
            "browser",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert (
        result.stderr
        == "stored session window readiness preflight could not be built\n"
    )


def test_session_window_readiness_preflight_command_delegates_to_helpers(
    capsys,
    monkeypatch,
) -> None:
    received: dict[str, object] = {}
    schedule_store_module = "async_scholar.schedule_store"
    scheduled_start_module = "async_scholar.scheduled_start"
    preflight_module = "async_scholar.session_window_readiness_preflight"
    fake_schedule_store_module = types.ModuleType(schedule_store_module)
    fake_scheduled_start_module = types.ModuleType(scheduled_start_module)
    fake_preflight_module = types.ModuleType(preflight_module)
    fake_store_payload = object()
    fake_clock = object()

    def fake_list(db_path: Path) -> object:
        received["db_path"] = db_path
        return fake_store_payload

    class FakeClock:
        def __new__(cls, **kwargs: object) -> object:
            received["clock_kwargs"] = kwargs
            return fake_clock

    def fake_build(
        stored_courses: object,
        archive_root: Path,
        session_id: str,
        source_kind: str,
        clock: object,
        *,
        enabled: bool,
    ) -> dict[str, object]:
        received["stored_courses"] = stored_courses
        received["archive_root"] = archive_root
        received["session_id"] = session_id
        received["source_kind"] = source_kind
        received["clock"] = clock
        received["enabled"] = enabled
        return {
            "status": "due",
            "session_id": "session-001",
            "source_kind": "file",
            "clock_day_of_week": "monday",
            "clock_local_time": "09:00",
            "course_count": 1,
            "due_count": 1,
            "alert_preview_count": 1,
            "archive_recovery_status": "partial",
            "archive_existing_count": 1,
            "archive_missing_count": 6,
            "archive_total_existing_size_bytes": 2,
            "ready_to_start": True,
            "artifacts": [{"filename": "events.jsonl", "size_bytes": 2}],
            "courses": [
                {
                    "course_id": "cs101",
                    "selected_class_time_index": 0,
                    "scheduled_day_of_week": "monday",
                    "scheduled_local_start_time": "09:00",
                    "due": True,
                    "minutes_until_start": 0,
                    "stop_after_minutes": 75,
                    "enabled": True,
                    "meeting_url": "https://meet.example.edu/token-secret",
                    "alert_preview": {
                        "alert_kind": "participation_check",
                        "delivery": "none",
                        "requires_confirmation": True,
                        "target": "private-device-token",
                    },
                }
            ],
        }

    fake_schedule_store_module.list_course_schedule_session_window_inputs = fake_list
    fake_scheduled_start_module.ScheduledStartClock = FakeClock
    fake_preflight_module.build_session_window_readiness_preflight_summary = fake_build
    monkeypatch.setitem(sys.modules, schedule_store_module, fake_schedule_store_module)
    monkeypatch.setitem(
        sys.modules,
        scheduled_start_module,
        fake_scheduled_start_module,
    )
    monkeypatch.setitem(sys.modules, preflight_module, fake_preflight_module)

    exit_code = cli.main(
        [
            "session-window-readiness-preflight-from-store-local",
            "session-001",
            "--db-path",
            "schedule.sqlite",
            "--archive-root",
            "archive-root",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out) == {
        "alert_preview_count": 1,
        "archive_existing_count": 1,
        "archive_missing_count": 6,
        "archive_recovery_status": "partial",
        "archive_total_existing_size_bytes": 2,
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 1,
        "courses": [
            {
                "alert_preview": {
                    "alert_kind": "participation_check",
                    "delivery": "none",
                    "requires_confirmation": True,
                },
                "course_id": "cs101",
                "due": True,
                "enabled": True,
                "minutes_until_start": 0,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "selected_class_time_index": 0,
                "stop_after_minutes": 75,
            }
        ],
        "due_count": 1,
        "ready_to_start": True,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "due",
    }
    assert captured.err == ""
    assert received == {
        "db_path": Path("schedule.sqlite"),
        "clock_kwargs": {"day_of_week": "monday", "local_time": "09:00"},
        "stored_courses": fake_store_payload,
        "archive_root": Path("archive-root"),
        "session_id": "session-001",
        "source_kind": "file",
        "clock": fake_clock,
        "enabled": True,
    }
    _assert_session_window_readiness_preflight_output_is_safe(
        captured.out,
        captured.err,
    )


def test_session_window_readiness_preflight_cli_requires_fixed_metadata() -> None:
    with pytest.raises(ValueError) as exc_info:
        cli._stored_session_window_readiness_preflight_safe_summary(
            {
                "status": "due",
                "session_id": "session-001",
                "source_kind": "file",
                "clock_day_of_week": "monday",
                "clock_local_time": "09:00",
                "course_count": 1,
                "due_count": 1,
                "alert_preview_count": 1,
                "archive_recovery_status": "partial",
                "archive_existing_count": 1,
                "archive_missing_count": 6,
                "archive_total_existing_size_bytes": 2,
                "ready_to_start": True,
                "courses": [
                    {
                        "course_id": "cs101",
                        "selected_class_time_index": 0,
                        "scheduled_day_of_week": "monday",
                        "scheduled_local_start_time": "09:00",
                        "due": True,
                        "minutes_until_start": 0,
                        "stop_after_minutes": 75,
                        "enabled": True,
                        "alert_preview": {
                            "alert_kind": "private-token",
                            "delivery": "none",
                            "requires_confirmation": True,
                        },
                    }
                ],
            }
        )

    assert (
        str(exc_info.value)
        == "stored session window readiness preflight could not be built"
    )


def test_session_window_readiness_preflight_handler_stays_read_only() -> None:
    source = inspect.getsource(
        cli._run_session_window_readiness_preflight_from_store_local_command
    )

    assert "list_course_schedule_session_window_inputs" in source
    assert "ScheduledStartClock" in source
    assert "build_session_window_readiness_preflight_summary" in source
    for forbidden_fragment in (
        "load_course_schedule(",
        "load_course_schedule_read_only",
        "load_course_schedule_safe_summary",
        "list_course_schedule_safe_summaries",
        "list_course_schedule_due_list_inputs",
        "load_course_schedule_session_stop_input",
        "save_course_schedule",
        "initialize_course_schedule_store",
        "_create_schema",
        "ScheduleConfig",
        "CourseMetadata",
        "datetime",
        "now(",
        "sleep",
        "Timer(",
        "threading",
        "asyncio",
        "subprocess",
        "webbrowser",
        "requests",
        "httpx",
        "playwright",
        "selenium",
        "sounddevice",
        "faster_whisper",
        "mic_recording",
        "telegram",
        "desktop_notifier",
        "execute_archive",
        "archive_delete",
        ".open(",
        ".read_text(",
        ".write_text(",
        ".mkdir(",
        ".unlink(",
        ".remove(",
        ".rmdir(",
        "rmtree",
    ):
        assert forbidden_fragment not in source


def test_session_stop_preview_from_store_local_requires_explicit_metadata() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-stop-preview-from-store-local",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr == "stored session stop preview could not be built\n"


def test_session_stop_preview_from_store_local_sanitizes_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-stop-preview-from-store-local",
            "C:\\Users\\student\\token-secret-auth-profile",
            "--db-path",
            "schedule.sqlite",
            "--course-id",
            "cs101",
            "--class-time-index",
            "0",
            "--source-kind",
            "file",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "stored session stop preview could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "unrecognized arguments",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_stop_preview_from_store_local_sanitizes_misordered_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--db-path",
            "C:\\Users\\student\\token-secret-auth-profile",
            "session-stop-preview-from-store-local",
            "--course-id",
            "cs101",
            "--class-time-index",
            "0",
            "--source-kind",
            "file",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "stored session stop preview could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "invalid choice",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_stop_preview_from_store_local_rejects_bad_source_kind(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-stop-preview-from-store-local",
            "--db-path",
            str(db_path),
            "--course-id",
            "cs101",
            "--class-time-index",
            "0",
            "--source-kind",
            "browser",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "stored session stop preview could not be built\n"
    for forbidden_fragment in (
        "browser",
        "invalid choice",
        str(tmp_path),
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_stop_preview_from_store_local_rejects_bad_disabled_input(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-stop-preview-from-store-local",
            "--db-path",
            str(db_path),
            "--course-id",
            "cs101",
            "--class-time-index",
            "0",
            "--source-kind",
            "file",
            "--disabled=false",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "stored session stop preview could not be built\n"
    for forbidden_fragment in (
        "false",
        "unrecognized arguments",
        str(tmp_path),
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_stop_preview_from_store_local_prints_safe_json(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)
    expected = {
        "course_id": "cs101",
        "enabled": True,
        "scheduled_day_of_week": "wednesday",
        "scheduled_local_start_time": "13:30",
        "selected_class_time_index": 1,
        "source_kind": "mic",
        "status": "enabled",
        "stop_after_minutes": 90,
    }

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-stop-preview-from-store-local",
            "--db-path",
            str(db_path),
            "--course-id",
            "cs101",
            "--class-time-index",
            "1",
            "--source-kind",
            "mic",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout == f"{json.dumps(expected, sort_keys=True)}\n"
    assert json.loads(result.stdout) == expected
    _assert_session_stop_preview_output_is_safe(result.stdout, result.stderr)


def test_session_stop_preview_from_store_local_prints_disabled_json(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-stop-preview-from-store-local",
            "--db-path",
            str(db_path),
            "--course-id",
            "cs101",
            "--class-time-index",
            "0",
            "--source-kind",
            "file",
            "--disabled",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert json.loads(result.stdout) == {
        "course_id": "cs101",
        "enabled": False,
        "scheduled_day_of_week": "monday",
        "scheduled_local_start_time": "09:00",
        "selected_class_time_index": 0,
        "source_kind": "file",
        "status": "disabled",
        "stop_after_minutes": 75,
    }
    _assert_session_stop_preview_output_is_safe(result.stdout, result.stderr)


def test_session_stop_preview_from_store_local_missing_db_does_not_create_file(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "missing-token-secret-auth-profile.sqlite"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-stop-preview-from-store-local",
            "--db-path",
            str(db_path),
            "--course-id",
            "cs101",
            "--class-time-index",
            "0",
            "--source-kind",
            "file",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "stored session stop preview could not be built\n"
    assert not db_path.exists()
    for forbidden_fragment in (
        str(tmp_path),
        "missing-token",
        "secret",
        "auth",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_stop_preview_from_store_local_sanitizes_missing_course(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-stop-preview-from-store-local",
            "--db-path",
            str(db_path),
            "--course-id",
            "missing-token-secret-auth-profile",
            "--class-time-index",
            "0",
            "--source-kind",
            "file",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "stored session stop preview could not be built\n"
    for forbidden_fragment in (
        str(tmp_path),
        "missing",
        "token",
        "secret",
        "auth",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_stop_preview_from_store_local_sanitizes_bad_index(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-stop-preview-from-store-local",
            "--db-path",
            str(db_path),
            "--course-id",
            "cs101",
            "--class-time-index",
            "99",
            "--source-kind",
            "file",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "stored session stop preview could not be built\n"
    for forbidden_fragment in (
        str(tmp_path),
        "99",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_stop_preview_from_store_local_sanitizes_malformed_store(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE courses (course_id TEXT PRIMARY KEY)")
        connection.execute("INSERT INTO courses (course_id) VALUES (?)", ("cs101",))

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-stop-preview-from-store-local",
            "--db-path",
            str(db_path),
            "--course-id",
            "cs101",
            "--class-time-index",
            "0",
            "--source-kind",
            "file",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "stored session stop preview could not be built\n"
    for forbidden_fragment in (
        str(tmp_path),
        "class_times",
        "select",
        "sqlite",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_stop_preview_from_store_local_command_delegates_to_helpers(
    capsys,
    monkeypatch,
) -> None:
    received: dict[str, object] = {}
    schedule_store_module = "async_scholar.schedule_store"
    session_stop_module = "async_scholar.session_stop"
    fake_schedule_store_module = types.ModuleType(schedule_store_module)
    fake_session_stop_module = types.ModuleType(session_stop_module)
    fake_store_payload = object()

    def fake_load(
        db_path: Path,
        course_id: str,
        selected_class_time_index: int,
    ) -> object:
        received["db_path"] = db_path
        received["course_id"] = course_id
        received["selected_class_time_index"] = selected_class_time_index
        return fake_store_payload

    def fake_build_preview(
        stored_class_time: object,
        source_kind: str,
        *,
        enabled: bool,
    ) -> dict[str, object]:
        received["stored_class_time"] = stored_class_time
        received["source_kind"] = source_kind
        received["enabled"] = enabled
        return {
            "status": "enabled",
            "course_id": "cs101",
            "source_kind": "file",
            "selected_class_time_index": 0,
            "scheduled_day_of_week": "monday",
            "scheduled_local_start_time": "09:00",
            "stop_after_minutes": 75,
            "enabled": True,
            "title": "Confidential Systems",
            "meeting_url": "https://meet.example.edu/token-secret",
        }

    fake_schedule_store_module.load_course_schedule_session_stop_input = fake_load
    fake_session_stop_module.build_session_stop_preview_from_store_input = (
        fake_build_preview
    )
    monkeypatch.setitem(sys.modules, schedule_store_module, fake_schedule_store_module)
    monkeypatch.setitem(sys.modules, session_stop_module, fake_session_stop_module)

    exit_code = cli.main(
        [
            "session-stop-preview-from-store-local",
            "--db-path",
            "schedule.sqlite",
            "--course-id",
            "cs101",
            "--class-time-index",
            "0",
            "--source-kind",
            "file",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out) == {
        "course_id": "cs101",
        "enabled": True,
        "scheduled_day_of_week": "monday",
        "scheduled_local_start_time": "09:00",
        "selected_class_time_index": 0,
        "source_kind": "file",
        "status": "enabled",
        "stop_after_minutes": 75,
    }
    assert captured.err == ""
    assert received == {
        "db_path": Path("schedule.sqlite"),
        "course_id": "cs101",
        "selected_class_time_index": 0,
        "stored_class_time": fake_store_payload,
        "source_kind": "file",
        "enabled": True,
    }
    _assert_session_stop_preview_output_is_safe(captured.out, captured.err)


def test_session_stop_preview_from_store_local_handler_stays_read_only() -> None:
    source = inspect.getsource(cli._run_session_stop_preview_from_store_local_command)

    assert "load_course_schedule_session_stop_input" in source
    assert "build_session_stop_preview_from_store_input" in source
    for forbidden_fragment in (
        "load_course_schedule(",
        "load_course_schedule_read_only",
        "load_course_schedule_safe_summary",
        "list_course_schedule_safe_summaries",
        "list_course_schedule_due_list_inputs",
        "save_course_schedule",
        "initialize_course_schedule_store",
        "_create_schema",
        "ScheduleConfig",
        "CourseMetadata",
        "ScheduledStartClock",
        "scheduled_start",
        "datetime",
        "now(",
        "sleep",
        "Timer(",
        "threading",
        "asyncio",
        "subprocess",
        "webbrowser",
        "requests",
        "httpx",
        "playwright",
        "selenium",
        "sounddevice",
        "faster_whisper",
        "mic_recording",
        "telegram",
        "desktop_notifier",
        "execute_archive",
        "archive_export",
        "archive_delete",
        ".open(",
        ".read_text(",
        ".write_text(",
        ".mkdir(",
        ".unlink(",
        ".remove(",
        ".rmdir(",
        "rmtree",
    ):
        assert forbidden_fragment not in source


def test_session_window_confirmation_preflight_from_store_local_help_stays_lazy(
    monkeypatch,
) -> None:
    schedule_store_module = "async_scholar.schedule_store"
    scheduled_start_module = "async_scholar.scheduled_start"
    preflight_module = "async_scholar.session_window_confirmation_preflight"
    monkeypatch.delitem(sys.modules, schedule_store_module, raising=False)
    monkeypatch.delitem(sys.modules, scheduled_start_module, raising=False)
    monkeypatch.delitem(sys.modules, preflight_module, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-confirmation-preflight-from-store-local",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert (
        "usage: async_scholar session-window-confirmation-preflight-from-store-local"
        in result.stdout
    )
    assert "--db-path" in result.stdout
    assert "--archive-root" in result.stdout
    assert "--clock-local-time" in result.stdout
    assert "read-only" in result.stdout
    assert schedule_store_module not in sys.modules
    assert scheduled_start_module not in sys.modules
    assert preflight_module not in sys.modules


def test_session_window_confirmation_preflight_from_store_local_requires_metadata() -> (
    None
):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-confirmation-preflight-from-store-local",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert (
        result.stderr
        == "stored session window confirmation preflight could not be built\n"
    )


def test_session_window_confirmation_preflight_from_store_local_prints_safe_json(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    archive_root = tmp_path / "archive"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    _write_private_course_schedule(db_path)
    (session_dir / "events.jsonl").write_text(
        "private event token secret auth profile payload",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-confirmation-preflight-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.count("\n") == 1
    assert json.loads(result.stdout) == {
        "blocked_execution_count": 1,
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "confirmation_required": True,
        "confirmation_status": "required",
        "course_count": 1,
        "courses": [
            {
                "course_id": "cs101",
                "due": True,
                "enabled": True,
                "minutes_until_start": 0,
                "requires_confirmation": True,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "selected_class_time_index": 0,
                "stop_after_minutes": 75,
            }
        ],
        "due_count": 1,
        "ready_to_start": True,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "required",
    }
    _assert_session_window_confirmation_preflight_output_is_safe(
        result.stdout,
        result.stderr,
    )


def test_session_window_confirmation_preflight_from_store_local_disabled(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    archive_root = tmp_path / "archive"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-confirmation-preflight-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "mic",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
            "--disabled",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout) == {
        "blocked_execution_count": 0,
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "confirmation_required": False,
        "confirmation_status": "disabled",
        "course_count": 1,
        "courses": [],
        "due_count": 0,
        "ready_to_start": False,
        "session_id": "session-001",
        "source_kind": "mic",
        "status": "disabled",
    }
    _assert_session_window_confirmation_preflight_output_is_safe(
        result.stdout,
        result.stderr,
    )


def test_session_window_confirmation_preflight_from_store_local_not_due(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    archive_root = tmp_path / "archive"
    (archive_root / "session-001").mkdir(parents=True)
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-confirmation-preflight-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "tuesday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout)["status"] == "not_required"
    assert json.loads(result.stdout)["confirmation_required"] is False
    assert json.loads(result.stdout)["blocked_execution_count"] == 0
    assert json.loads(result.stdout)["courses"] == []
    _assert_session_window_confirmation_preflight_output_is_safe(
        result.stdout,
        result.stderr,
    )


def test_session_window_confirmation_preflight_from_store_local_sanitizes_db_failure(
    tmp_path: Path,
) -> None:
    missing_db_path = tmp_path / "missing-token-secret-auth-profile.sqlite"
    archive_root = tmp_path / "archive"
    (archive_root / "session-001").mkdir(parents=True)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-confirmation-preflight-from-store-local",
            "session-001",
            "--db-path",
            str(missing_db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert (
        result.stderr
        == "stored session window confirmation preflight could not be built\n"
    )
    assert not missing_db_path.exists()
    for forbidden_fragment in (
        str(tmp_path),
        "missing-token",
        "secret",
        "auth",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_window_confirmation_preflight_from_store_local_sanitizes_malformed_db(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    archive_root = tmp_path / "archive"
    (archive_root / "session-001").mkdir(parents=True)
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE courses (course_id TEXT PRIMARY KEY)")
        connection.execute("INSERT INTO courses (course_id) VALUES (?)", ("cs101",))

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-confirmation-preflight-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert (
        result.stderr
        == "stored session window confirmation preflight could not be built\n"
    )
    for forbidden_fragment in (
        str(tmp_path),
        "class_times",
        "select",
        "sqlite",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_window_confirmation_preflight_sanitizes_archive_failure(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    archive_root = tmp_path / "archive-token-secret-auth-profile"
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-confirmation-preflight-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert (
        result.stderr
        == "stored session window confirmation preflight could not be built\n"
    )
    assert not archive_root.exists()
    for forbidden_fragment in (
        str(tmp_path),
        "archive-token",
        "secret",
        "auth",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_window_confirmation_preflight_from_store_local_rejects_source() -> (
    None
):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-confirmation-preflight-from-store-local",
            "session-001",
            "--db-path",
            "schedule.sqlite",
            "--archive-root",
            "archive",
            "--source-kind",
            "browser",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert (
        result.stderr
        == "stored session window confirmation preflight could not be built\n"
    )


def test_session_window_confirmation_preflight_command_delegates_to_helpers(
    capsys,
    monkeypatch,
) -> None:
    received: dict[str, object] = {}
    schedule_store_module = "async_scholar.schedule_store"
    scheduled_start_module = "async_scholar.scheduled_start"
    preflight_module = "async_scholar.session_window_confirmation_preflight"
    fake_schedule_store_module = types.ModuleType(schedule_store_module)
    fake_scheduled_start_module = types.ModuleType(scheduled_start_module)
    fake_preflight_module = types.ModuleType(preflight_module)
    fake_store_payload = object()
    fake_clock = object()

    def fake_list(db_path: Path) -> object:
        received["db_path"] = db_path
        return fake_store_payload

    class FakeClock:
        def __new__(cls, **kwargs: object) -> object:
            received["clock_kwargs"] = kwargs
            return fake_clock

    def fake_build(
        stored_courses: object,
        archive_root: Path,
        session_id: str,
        source_kind: str,
        clock: object,
        *,
        enabled: bool,
    ) -> dict[str, object]:
        received["stored_courses"] = stored_courses
        received["archive_root"] = archive_root
        received["session_id"] = session_id
        received["source_kind"] = source_kind
        received["clock"] = clock
        received["enabled"] = enabled
        return {
            "status": "required",
            "session_id": "session-001",
            "source_kind": "file",
            "clock_day_of_week": "monday",
            "clock_local_time": "09:00",
            "course_count": 1,
            "due_count": 1,
            "ready_to_start": True,
            "confirmation_required": True,
            "confirmation_status": "required",
            "blocked_execution_count": 1,
            "archive_existing_count": 1,
            "alert_preview_count": 1,
            "artifacts": [{"filename": "events.jsonl", "size_bytes": 2}],
            "courses": [
                {
                    "course_id": "cs101",
                    "selected_class_time_index": 0,
                    "scheduled_day_of_week": "monday",
                    "scheduled_local_start_time": "09:00",
                    "due": True,
                    "minutes_until_start": 0,
                    "stop_after_minutes": 75,
                    "enabled": True,
                    "requires_confirmation": True,
                    "meeting_url": "https://meet.example.edu/token-secret",
                    "alert_preview": {
                        "alert_kind": "participation_check",
                        "delivery": "none",
                        "requires_confirmation": True,
                    },
                }
            ],
        }

    fake_schedule_store_module.list_course_schedule_session_window_inputs = fake_list
    fake_scheduled_start_module.ScheduledStartClock = FakeClock
    fake_preflight_module.build_session_window_confirmation_preflight_summary = (
        fake_build
    )
    monkeypatch.setitem(sys.modules, schedule_store_module, fake_schedule_store_module)
    monkeypatch.setitem(
        sys.modules,
        scheduled_start_module,
        fake_scheduled_start_module,
    )
    monkeypatch.setitem(sys.modules, preflight_module, fake_preflight_module)

    exit_code = cli.main(
        [
            "session-window-confirmation-preflight-from-store-local",
            "session-001",
            "--db-path",
            "schedule.sqlite",
            "--archive-root",
            "archive-root",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out) == {
        "blocked_execution_count": 1,
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "confirmation_required": True,
        "confirmation_status": "required",
        "course_count": 1,
        "courses": [
            {
                "course_id": "cs101",
                "due": True,
                "enabled": True,
                "minutes_until_start": 0,
                "requires_confirmation": True,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "selected_class_time_index": 0,
                "stop_after_minutes": 75,
            }
        ],
        "due_count": 1,
        "ready_to_start": True,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "required",
    }
    assert captured.err == ""
    assert received == {
        "db_path": Path("schedule.sqlite"),
        "clock_kwargs": {"day_of_week": "monday", "local_time": "09:00"},
        "stored_courses": fake_store_payload,
        "archive_root": Path("archive-root"),
        "session_id": "session-001",
        "source_kind": "file",
        "clock": fake_clock,
        "enabled": True,
    }
    _assert_session_window_confirmation_preflight_output_is_safe(
        captured.out,
        captured.err,
    )


def test_session_window_confirmation_preflight_cli_requires_fixed_policy() -> None:
    payload: dict[str, object] = {
        "status": "required",
        "session_id": "session-001",
        "source_kind": "file",
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 1,
        "due_count": 1,
        "ready_to_start": True,
        "confirmation_required": True,
        "confirmation_status": "not_required",
        "blocked_execution_count": 1,
        "courses": [
            {
                "course_id": "cs101",
                "selected_class_time_index": 0,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "due": True,
                "minutes_until_start": 0,
                "stop_after_minutes": 75,
                "enabled": True,
                "requires_confirmation": True,
            }
        ],
    }

    with pytest.raises(ValueError) as exc_info:
        cli._stored_session_window_confirmation_preflight_safe_summary(payload)

    assert (
        str(exc_info.value)
        == "stored session window confirmation preflight could not be built"
    )


def test_session_window_confirmation_preflight_handler_stays_read_only() -> None:
    source = inspect.getsource(
        cli._run_session_window_confirmation_preflight_from_store_local_command
    )

    assert "list_course_schedule_session_window_inputs" in source
    assert "ScheduledStartClock" in source
    assert "build_session_window_confirmation_preflight_summary" in source
    for forbidden_fragment in (
        "load_course_schedule(",
        "load_course_schedule_read_only",
        "load_course_schedule_safe_summary",
        "list_course_schedule_safe_summaries",
        "list_course_schedule_due_list_inputs",
        "load_course_schedule_session_stop_input",
        "save_course_schedule",
        "initialize_course_schedule_store",
        "_create_schema",
        "ScheduleConfig",
        "CourseMetadata",
        "datetime",
        "now(",
        "sleep",
        "Timer(",
        "threading",
        "asyncio",
        "subprocess",
        "webbrowser",
        "requests",
        "httpx",
        "playwright",
        "selenium",
        "sounddevice",
        "faster_whisper",
        "mic_recording",
        "telegram",
        "desktop_notifier",
        "execute_archive",
        "archive_delete",
        ".open(",
        ".read_text(",
        ".write_text(",
        ".mkdir(",
        ".unlink(",
        ".remove(",
        ".rmdir(",
        "rmtree",
    ):
        assert forbidden_fragment not in source


def test_session_window_confirmation_response_from_store_local_help_stays_lazy(
    monkeypatch,
) -> None:
    schedule_store_module = "async_scholar.schedule_store"
    scheduled_start_module = "async_scholar.scheduled_start"
    preflight_module = "async_scholar.session_window_confirmation_preflight"
    response_module = "async_scholar.session_window_confirmation_response"
    monkeypatch.delitem(sys.modules, schedule_store_module, raising=False)
    monkeypatch.delitem(sys.modules, scheduled_start_module, raising=False)
    monkeypatch.delitem(sys.modules, preflight_module, raising=False)
    monkeypatch.delitem(sys.modules, response_module, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-confirmation-response-from-store-local",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert (
        "usage: async_scholar session-window-confirmation-response-from-store-local"
        in result.stdout
    )
    assert "--db-path" in result.stdout
    assert "--archive-root" in result.stdout
    assert "--clock-local-time" in result.stdout
    assert "--confirmation-response" in result.stdout
    assert "confirmed" in result.stdout
    assert "declined" in result.stdout
    assert "non-executing" in result.stdout
    assert schedule_store_module not in sys.modules
    assert scheduled_start_module not in sys.modules
    assert preflight_module not in sys.modules
    assert response_module not in sys.modules


def test_session_window_confirmation_response_from_store_local_requires_metadata() -> (
    None
):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-confirmation-response-from-store-local",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert (
        result.stderr
        == "stored session window confirmation response could not be built\n"
    )


def test_session_window_confirmation_response_from_store_local_prints_confirmed_json(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    archive_root = tmp_path / "archive"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    _write_private_course_schedule(db_path)
    (session_dir / "events.jsonl").write_text(
        "private event token secret auth profile payload",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-confirmation-response-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
            "--confirmation-response",
            "confirmed",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.count("\n") == 1
    assert json.loads(result.stdout) == {
        "blocked_execution_count": 0,
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "confirmation_required": True,
        "confirmation_response": "confirmed",
        "confirmation_status": "required",
        "confirmation_verified": True,
        "confirmed_start_count": 1,
        "course_count": 1,
        "courses": [
            {
                "confirmation_response": "confirmed",
                "course_id": "cs101",
                "due": True,
                "enabled": True,
                "minutes_until_start": 0,
                "requires_confirmation": True,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "selected_class_time_index": 0,
                "stop_after_minutes": 75,
            }
        ],
        "due_count": 1,
        "ready_to_start": True,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "confirmed",
    }
    _assert_session_window_confirmation_response_output_is_safe(
        result.stdout,
        result.stderr,
    )


def test_session_window_confirmation_response_from_store_local_prints_declined_json(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    archive_root = tmp_path / "archive"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    _write_private_course_schedule(db_path)
    (session_dir / "events.jsonl").write_text(
        "private event token secret auth profile payload",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-confirmation-response-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "mic",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
            "--confirmation-response",
            "declined",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert result.stderr == ""
    assert payload["status"] == "declined"
    assert payload["confirmation_verified"] is False
    assert payload["confirmed_start_count"] == 0
    assert payload["blocked_execution_count"] == payload["due_count"] == 1
    assert payload["courses"][0]["confirmation_response"] == "declined"
    assert payload["source_kind"] == "mic"
    _assert_session_window_confirmation_response_output_is_safe(
        result.stdout,
        result.stderr,
    )


def test_session_window_confirmation_response_from_store_local_disabled(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    archive_root = tmp_path / "archive"
    (archive_root / "session-001").mkdir(parents=True)
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-confirmation-response-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
            "--confirmation-response",
            "confirmed",
            "--disabled",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout) == {
        "blocked_execution_count": 0,
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "confirmation_required": False,
        "confirmation_response": "confirmed",
        "confirmation_status": "disabled",
        "confirmation_verified": False,
        "confirmed_start_count": 0,
        "course_count": 1,
        "courses": [],
        "due_count": 0,
        "ready_to_start": False,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "disabled",
    }
    _assert_session_window_confirmation_response_output_is_safe(
        result.stdout,
        result.stderr,
    )


def test_session_window_confirmation_response_from_store_local_not_required(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    archive_root = tmp_path / "archive"
    (archive_root / "session-001").mkdir(parents=True)
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-confirmation-response-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "tuesday",
            "--clock-local-time",
            "09:00",
            "--confirmation-response",
            "declined",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["status"] == "not_required"
    assert payload["confirmation_verified"] is False
    assert payload["confirmed_start_count"] == 0
    assert payload["blocked_execution_count"] == 0
    assert payload["courses"] == []
    _assert_session_window_confirmation_response_output_is_safe(
        result.stdout,
        result.stderr,
    )


def test_session_window_confirmation_response_from_store_local_sanitizes_db_failure(
    tmp_path: Path,
) -> None:
    missing_db_path = tmp_path / "missing-token-secret-auth-profile.sqlite"
    archive_root = tmp_path / "archive"
    (archive_root / "session-001").mkdir(parents=True)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-confirmation-response-from-store-local",
            "session-001",
            "--db-path",
            str(missing_db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
            "--confirmation-response",
            "confirmed",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert (
        result.stderr
        == "stored session window confirmation response could not be built\n"
    )
    assert not missing_db_path.exists()
    for forbidden_fragment in (
        str(tmp_path),
        "missing-token",
        "secret",
        "auth",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_window_confirmation_response_sanitizes_archive_failure(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    archive_root = tmp_path / "archive-token-secret-auth-profile"
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-confirmation-response-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
            "--confirmation-response",
            "declined",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert (
        result.stderr
        == "stored session window confirmation response could not be built\n"
    )
    assert not archive_root.exists()
    for forbidden_fragment in (
        str(tmp_path),
        "archive-token",
        "secret",
        "auth",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_window_confirmation_response_rejects_free_form_response() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-confirmation-response-from-store-local",
            "session-001",
            "--db-path",
            "schedule.sqlite",
            "--archive-root",
            "archive",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
            "--confirmation-response",
            "yes please start this class",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert (
        result.stderr
        == "stored session window confirmation response could not be built\n"
    )


def test_session_window_confirmation_response_misordered_uses_response_error() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--archive-root",
            "C:\\Users\\student\\token-secret-auth-profile",
            "session-window-confirmation-response-from-store-local",
            "session-001",
            "--db-path",
            "C:\\Users\\student\\private.sqlite",
            "--confirmation-response",
            "confirmed",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert (
        result.stderr
        == "stored session window confirmation response could not be built\n"
    )
    for forbidden_fragment in (
        "C:\\Users",
        "token",
        "secret",
        "auth",
        "profile",
        "private.sqlite",
        "archive preflight",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_window_confirmation_response_command_delegates_to_helpers(
    capsys,
    monkeypatch,
) -> None:
    received: dict[str, object] = {}
    schedule_store_module = "async_scholar.schedule_store"
    scheduled_start_module = "async_scholar.scheduled_start"
    preflight_module = "async_scholar.session_window_confirmation_preflight"
    response_module = "async_scholar.session_window_confirmation_response"
    fake_schedule_store_module = types.ModuleType(schedule_store_module)
    fake_scheduled_start_module = types.ModuleType(scheduled_start_module)
    fake_preflight_module = types.ModuleType(preflight_module)
    fake_response_module = types.ModuleType(response_module)
    fake_store_payload = object()
    fake_clock = object()

    def fake_list(db_path: Path) -> object:
        received["db_path"] = db_path
        return fake_store_payload

    class FakeClock:
        def __new__(cls, **kwargs: object) -> object:
            received["clock_kwargs"] = kwargs
            return fake_clock

    def fake_build_preflight(
        stored_courses: object,
        archive_root: Path,
        session_id: str,
        source_kind: str,
        clock: object,
        *,
        enabled: bool,
    ) -> dict[str, object]:
        received["stored_courses"] = stored_courses
        received["archive_root"] = archive_root
        received["session_id"] = session_id
        received["source_kind"] = source_kind
        received["clock"] = clock
        received["enabled"] = enabled
        return {
            "status": "required",
            "session_id": "session-001",
            "source_kind": "file",
            "clock_day_of_week": "monday",
            "clock_local_time": "09:00",
            "course_count": 1,
            "due_count": 1,
            "ready_to_start": True,
            "confirmation_required": True,
            "confirmation_status": "required",
            "blocked_execution_count": 1,
            "archive_existing_count": 1,
            "alert_preview_count": 1,
            "courses": [
                {
                    "course_id": "cs101",
                    "selected_class_time_index": 0,
                    "scheduled_day_of_week": "monday",
                    "scheduled_local_start_time": "09:00",
                    "due": True,
                    "minutes_until_start": 0,
                    "stop_after_minutes": 75,
                    "enabled": True,
                    "requires_confirmation": True,
                    "meeting_url": "https://meet.example.edu/token-secret",
                }
            ],
        }

    def fake_build_response(
        preflight_summary: dict[str, object],
        confirmation_response: str,
    ) -> dict[str, object]:
        received["preflight_summary"] = preflight_summary
        received["confirmation_response"] = confirmation_response
        return {
            "status": "confirmed",
            "session_id": "session-001",
            "source_kind": "file",
            "clock_day_of_week": "monday",
            "clock_local_time": "09:00",
            "course_count": 1,
            "due_count": 1,
            "ready_to_start": True,
            "confirmation_required": True,
            "confirmation_status": "required",
            "confirmation_response": "confirmed",
            "confirmation_verified": True,
            "confirmed_start_count": 1,
            "blocked_execution_count": 0,
            "meeting_url": "https://meet.example.edu/token-secret",
            "courses": [
                {
                    "course_id": "cs101",
                    "selected_class_time_index": 0,
                    "scheduled_day_of_week": "monday",
                    "scheduled_local_start_time": "09:00",
                    "due": True,
                    "minutes_until_start": 0,
                    "stop_after_minutes": 75,
                    "enabled": True,
                    "requires_confirmation": True,
                    "confirmation_response": "confirmed",
                    "meeting_url": "https://meet.example.edu/token-secret",
                }
            ],
        }

    fake_schedule_store_module.list_course_schedule_session_window_inputs = fake_list
    fake_scheduled_start_module.ScheduledStartClock = FakeClock
    fake_preflight_module.build_session_window_confirmation_preflight_summary = (
        fake_build_preflight
    )
    fake_response_module.build_session_window_confirmation_response_summary = (
        fake_build_response
    )
    monkeypatch.setitem(sys.modules, schedule_store_module, fake_schedule_store_module)
    monkeypatch.setitem(
        sys.modules,
        scheduled_start_module,
        fake_scheduled_start_module,
    )
    monkeypatch.setitem(sys.modules, preflight_module, fake_preflight_module)
    monkeypatch.setitem(sys.modules, response_module, fake_response_module)

    exit_code = cli.main(
        [
            "session-window-confirmation-response-from-store-local",
            "session-001",
            "--db-path",
            "schedule.sqlite",
            "--archive-root",
            "archive-root",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
            "--confirmation-response",
            "confirmed",
        ],
    )

    captured = capsys.readouterr()
    preflight_summary = received["preflight_summary"]
    assert exit_code == 0
    assert json.loads(captured.out) == {
        "blocked_execution_count": 0,
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "confirmation_required": True,
        "confirmation_response": "confirmed",
        "confirmation_status": "required",
        "confirmation_verified": True,
        "confirmed_start_count": 1,
        "course_count": 1,
        "courses": [
            {
                "confirmation_response": "confirmed",
                "course_id": "cs101",
                "due": True,
                "enabled": True,
                "minutes_until_start": 0,
                "requires_confirmation": True,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "selected_class_time_index": 0,
                "stop_after_minutes": 75,
            }
        ],
        "due_count": 1,
        "ready_to_start": True,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "confirmed",
    }
    assert captured.err == ""
    assert received == {
        "db_path": Path("schedule.sqlite"),
        "clock_kwargs": {"day_of_week": "monday", "local_time": "09:00"},
        "stored_courses": fake_store_payload,
        "archive_root": Path("archive-root"),
        "session_id": "session-001",
        "source_kind": "file",
        "clock": fake_clock,
        "enabled": True,
        "preflight_summary": preflight_summary,
        "confirmation_response": "confirmed",
    }
    _assert_session_window_confirmation_response_output_is_safe(
        captured.out,
        captured.err,
    )


def test_session_window_confirmation_response_cli_requires_fixed_policy() -> None:
    payload: dict[str, object] = {
        "status": "confirmed",
        "session_id": "session-001",
        "source_kind": "file",
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 1,
        "due_count": 1,
        "ready_to_start": True,
        "confirmation_required": True,
        "confirmation_status": "required",
        "confirmation_response": "custom free-form response",
        "confirmation_verified": True,
        "confirmed_start_count": 1,
        "blocked_execution_count": 0,
        "courses": [],
    }

    with pytest.raises(ValueError) as exc_info:
        cli._stored_session_window_confirmation_response_safe_summary(payload)

    assert (
        str(exc_info.value)
        == "stored session window confirmation response could not be built"
    )


def test_session_window_confirmation_response_handler_stays_read_only() -> None:
    source = inspect.getsource(
        cli._run_session_window_confirmation_response_from_store_local_command
    )

    assert "list_course_schedule_session_window_inputs" in source
    assert "ScheduledStartClock" in source
    assert "build_session_window_confirmation_preflight_summary" in source
    assert "build_session_window_confirmation_response_summary" in source
    for forbidden_fragment in (
        "_stored_session_window_confirmation_preflight_safe_summary",
        "load_course_schedule(",
        "load_course_schedule_read_only",
        "load_course_schedule_safe_summary",
        "list_course_schedule_safe_summaries",
        "list_course_schedule_due_list_inputs",
        "load_course_schedule_session_stop_input",
        "save_course_schedule",
        "initialize_course_schedule_store",
        "_create_schema",
        "ScheduleConfig",
        "CourseMetadata",
        "datetime",
        "now(",
        "sleep",
        "Timer(",
        "threading",
        "asyncio",
        "subprocess",
        "webbrowser",
        "requests",
        "httpx",
        "playwright",
        "selenium",
        "sounddevice",
        "faster_whisper",
        "mic_recording",
        "telegram",
        "desktop_notifier",
        "execute_archive",
        "archive_delete",
        ".open(",
        ".read_text(",
        ".write_text(",
        ".mkdir(",
        ".unlink(",
        ".remove(",
        ".rmdir(",
        "rmtree",
    ):
        assert forbidden_fragment not in source


def test_session_window_start_authorization_from_store_local_help_stays_lazy(
    monkeypatch,
) -> None:
    schedule_store_module = "async_scholar.schedule_store"
    scheduled_start_module = "async_scholar.scheduled_start"
    preflight_module = "async_scholar.session_window_confirmation_preflight"
    response_module = "async_scholar.session_window_confirmation_response"
    authorization_module = "async_scholar.session_window_start_authorization"
    monkeypatch.delitem(sys.modules, schedule_store_module, raising=False)
    monkeypatch.delitem(sys.modules, scheduled_start_module, raising=False)
    monkeypatch.delitem(sys.modules, preflight_module, raising=False)
    monkeypatch.delitem(sys.modules, response_module, raising=False)
    monkeypatch.delitem(sys.modules, authorization_module, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-start-authorization-from-store-local",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert (
        "usage: async_scholar session-window-start-authorization-from-store-local"
        in result.stdout
    )
    assert "--db-path" in result.stdout
    assert "--archive-root" in result.stdout
    assert "--source-kind" in result.stdout
    assert "--clock-day-of-week" in result.stdout
    assert "--clock-local-time" in result.stdout
    assert "--confirmation-response" in result.stdout
    assert "confirmed" in result.stdout
    assert "declined" in result.stdout
    assert "non-executing" in result.stdout
    assert schedule_store_module not in sys.modules
    assert scheduled_start_module not in sys.modules
    assert preflight_module not in sys.modules
    assert response_module not in sys.modules
    assert authorization_module not in sys.modules


def test_session_window_start_authorization_from_store_local_requires_metadata() -> (
    None
):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-start-authorization-from-store-local",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert (
        result.stderr
        == "stored session window start authorization could not be built\n"
    )


def test_session_window_start_authorization_prints_confirmed_json(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    archive_root = tmp_path / "archive"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    _write_private_course_schedule(db_path)
    (session_dir / "events.jsonl").write_text(
        "private event token secret auth profile payload",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-start-authorization-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
            "--confirmation-response",
            "confirmed",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    expected = {
        "authorized": True,
        "authorized_start_count": 1,
        "block_reason": "none",
        "blocked_start_count": 0,
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "confirmation_required": True,
        "confirmation_response": "confirmed",
        "confirmation_status": "required",
        "confirmation_verified": True,
        "course_count": 1,
        "courses": [
            {
                "authorized": True,
                "confirmation_response": "confirmed",
                "course_id": "cs101",
                "due": True,
                "enabled": True,
                "minutes_until_start": 0,
                "requires_confirmation": True,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "selected_class_time_index": 0,
                "stop_after_minutes": 75,
            }
        ],
        "due_count": 1,
        "ready_to_start": True,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "authorized",
    }
    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout == json.dumps(expected, sort_keys=True) + "\n"
    assert json.loads(result.stdout) == expected
    _assert_session_window_start_authorization_output_is_safe(
        result.stdout,
        result.stderr,
    )


def test_session_window_start_authorization_prints_declined_json(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    archive_root = tmp_path / "archive"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    _write_private_course_schedule(db_path)
    (session_dir / "events.jsonl").write_text(
        "private event token secret auth profile payload",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-start-authorization-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "mic",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
            "--confirmation-response",
            "declined",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert result.stderr == ""
    assert payload["status"] == "blocked"
    assert payload["source_kind"] == "mic"
    assert payload["confirmation_response"] == "declined"
    assert payload["confirmation_verified"] is False
    assert payload["authorized"] is False
    assert payload["authorized_start_count"] == 0
    assert payload["blocked_start_count"] == payload["due_count"] == 1
    assert payload["block_reason"] == "confirmation_declined"
    assert payload["courses"] == []
    _assert_session_window_start_authorization_output_is_safe(
        result.stdout,
        result.stderr,
    )


def test_session_window_start_authorization_from_store_local_disabled(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    archive_root = tmp_path / "archive"
    (archive_root / "session-001").mkdir(parents=True)
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-start-authorization-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
            "--confirmation-response",
            "confirmed",
            "--disabled",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["authorized"] is False
    assert payload["authorized_start_count"] == 0
    assert payload["blocked_start_count"] == 0
    assert payload["courses"] == []
    assert payload["ready_to_start"] is False
    assert payload["confirmation_verified"] is False
    assert payload["confirmation_required"] is False
    _assert_session_window_start_authorization_output_is_safe(
        result.stdout,
        result.stderr,
    )


def test_session_window_start_authorization_from_store_local_not_required(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    archive_root = tmp_path / "archive"
    (archive_root / "session-001").mkdir(parents=True)
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-start-authorization-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "tuesday",
            "--clock-local-time",
            "09:00",
            "--confirmation-response",
            "confirmed",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["authorized"] is False
    assert payload["authorized_start_count"] == 0
    assert payload["blocked_start_count"] == 0
    assert payload["courses"] == []
    assert payload["confirmation_required"] is False
    assert payload["confirmation_verified"] is False
    _assert_session_window_start_authorization_output_is_safe(
        result.stdout,
        result.stderr,
    )


def test_session_window_start_authorization_sanitizes_db_failure(
    tmp_path: Path,
) -> None:
    missing_db_path = tmp_path / "missing-token-secret-auth-profile.sqlite"
    archive_root = tmp_path / "archive"
    (archive_root / "session-001").mkdir(parents=True)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-start-authorization-from-store-local",
            "session-001",
            "--db-path",
            str(missing_db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
            "--confirmation-response",
            "confirmed",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert (
        result.stderr
        == "stored session window start authorization could not be built\n"
    )
    assert not missing_db_path.exists()
    for forbidden_fragment in (
        str(tmp_path),
        "missing-token",
        "secret",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_window_start_authorization_sanitizes_archive_failure(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    archive_root = tmp_path / "archive-token-secret-auth-profile"
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-start-authorization-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
            "--confirmation-response",
            "confirmed",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert (
        result.stderr
        == "stored session window start authorization could not be built\n"
    )
    assert not archive_root.exists()
    for forbidden_fragment in (
        str(tmp_path),
        "archive-token",
        "secret",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_window_start_authorization_rejects_free_form_response() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-start-authorization-from-store-local",
            "session-001",
            "--db-path",
            "schedule.sqlite",
            "--archive-root",
            "archive",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
            "--confirmation-response",
            "yes please start this class",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert (
        result.stderr
        == "stored session window start authorization could not be built\n"
    )


def test_session_window_start_authorization_misordered_uses_auth_error() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--archive-root",
            "C:\\Users\\student\\token-secret-auth-profile",
            "session-window-start-authorization-from-store-local",
            "session-001",
            "--db-path",
            "C:\\Users\\student\\private.sqlite",
            "--confirmation-response",
            "confirmed",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert (
        result.stderr
        == "stored session window start authorization could not be built\n"
    )
    for forbidden_fragment in (
        "C:\\Users",
        "token",
        "secret",
        "profile",
        "private.sqlite",
        "archive preflight",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_window_start_authorization_command_delegates_to_helpers(
    capsys,
    monkeypatch,
) -> None:
    received: dict[str, object] = {}
    schedule_store_module = "async_scholar.schedule_store"
    scheduled_start_module = "async_scholar.scheduled_start"
    preflight_module = "async_scholar.session_window_confirmation_preflight"
    response_module = "async_scholar.session_window_confirmation_response"
    authorization_module = "async_scholar.session_window_start_authorization"
    fake_schedule_store_module = types.ModuleType(schedule_store_module)
    fake_scheduled_start_module = types.ModuleType(scheduled_start_module)
    fake_preflight_module = types.ModuleType(preflight_module)
    fake_response_module = types.ModuleType(response_module)
    fake_authorization_module = types.ModuleType(authorization_module)
    fake_store_payload = object()
    fake_clock = object()

    def fake_list(db_path: Path) -> object:
        received["db_path"] = db_path
        return fake_store_payload

    class FakeClock:
        def __new__(cls, **kwargs: object) -> object:
            received["clock_kwargs"] = kwargs
            return fake_clock

    def fake_build_preflight(
        stored_courses: object,
        archive_root: Path,
        session_id: str,
        source_kind: str,
        clock: object,
        *,
        enabled: bool,
    ) -> dict[str, object]:
        received["stored_courses"] = stored_courses
        received["archive_root"] = archive_root
        received["session_id"] = session_id
        received["source_kind"] = source_kind
        received["clock"] = clock
        received["enabled"] = enabled
        return {
            "status": "required",
            "session_id": "session-001",
            "source_kind": "file",
            "clock_day_of_week": "monday",
            "clock_local_time": "09:00",
            "course_count": 1,
            "due_count": 1,
            "ready_to_start": True,
            "confirmation_required": True,
            "confirmation_status": "required",
            "blocked_execution_count": 1,
            "archive_existing_count": 1,
            "alert_preview_count": 1,
            "courses": [
                {
                    "course_id": "cs101",
                    "selected_class_time_index": 0,
                    "scheduled_day_of_week": "monday",
                    "scheduled_local_start_time": "09:00",
                    "due": True,
                    "minutes_until_start": 0,
                    "stop_after_minutes": 75,
                    "enabled": True,
                    "requires_confirmation": True,
                    "meeting_url": "https://meet.example.edu/token-secret",
                }
            ],
        }

    def fake_build_response(
        preflight_summary: dict[str, object],
        confirmation_response: str,
    ) -> dict[str, object]:
        received["preflight_summary"] = preflight_summary
        received["confirmation_response"] = confirmation_response
        return {
            "status": "confirmed",
            "session_id": "session-001",
            "source_kind": "file",
            "clock_day_of_week": "monday",
            "clock_local_time": "09:00",
            "course_count": 1,
            "due_count": 1,
            "ready_to_start": True,
            "confirmation_required": True,
            "confirmation_status": "required",
            "confirmation_response": "confirmed",
            "confirmation_verified": True,
            "confirmed_start_count": 1,
            "blocked_execution_count": 0,
            "meeting_url": "https://meet.example.edu/token-secret",
            "courses": [
                {
                    "course_id": "cs101",
                    "selected_class_time_index": 0,
                    "scheduled_day_of_week": "monday",
                    "scheduled_local_start_time": "09:00",
                    "due": True,
                    "minutes_until_start": 0,
                    "stop_after_minutes": 75,
                    "enabled": True,
                    "requires_confirmation": True,
                    "confirmation_response": "confirmed",
                    "meeting_url": "https://meet.example.edu/token-secret",
                }
            ],
        }

    def fake_build_authorization(
        response_summary: dict[str, object],
    ) -> dict[str, object]:
        received["response_summary"] = response_summary
        return {
            "status": "authorized",
            "session_id": "session-001",
            "source_kind": "file",
            "clock_day_of_week": "monday",
            "clock_local_time": "09:00",
            "course_count": 1,
            "due_count": 1,
            "ready_to_start": True,
            "confirmation_required": True,
            "confirmation_status": "required",
            "confirmation_response": "confirmed",
            "confirmation_verified": True,
            "authorized": True,
            "authorized_start_count": 1,
            "blocked_start_count": 0,
            "block_reason": "none",
            "meeting_url": "https://meet.example.edu/token-secret",
            "courses": [
                {
                    "course_id": "cs101",
                    "selected_class_time_index": 0,
                    "scheduled_day_of_week": "monday",
                    "scheduled_local_start_time": "09:00",
                    "due": True,
                    "minutes_until_start": 0,
                    "stop_after_minutes": 75,
                    "enabled": True,
                    "requires_confirmation": True,
                    "confirmation_response": "confirmed",
                    "authorized": True,
                    "meeting_url": "https://meet.example.edu/token-secret",
                }
            ],
        }

    fake_schedule_store_module.list_course_schedule_session_window_inputs = fake_list
    fake_scheduled_start_module.ScheduledStartClock = FakeClock
    fake_preflight_module.build_session_window_confirmation_preflight_summary = (
        fake_build_preflight
    )
    fake_response_module.build_session_window_confirmation_response_summary = (
        fake_build_response
    )
    fake_authorization_module.build_session_window_start_authorization_summary = (
        fake_build_authorization
    )
    monkeypatch.setitem(sys.modules, schedule_store_module, fake_schedule_store_module)
    monkeypatch.setitem(
        sys.modules,
        scheduled_start_module,
        fake_scheduled_start_module,
    )
    monkeypatch.setitem(sys.modules, preflight_module, fake_preflight_module)
    monkeypatch.setitem(sys.modules, response_module, fake_response_module)
    monkeypatch.setitem(sys.modules, authorization_module, fake_authorization_module)

    exit_code = cli.main(
        [
            "session-window-start-authorization-from-store-local",
            "session-001",
            "--db-path",
            "schedule.sqlite",
            "--archive-root",
            "archive-root",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
            "--confirmation-response",
            "confirmed",
        ],
    )

    captured = capsys.readouterr()
    preflight_summary = received["preflight_summary"]
    response_summary = received["response_summary"]
    assert exit_code == 0
    assert json.loads(captured.out) == {
        "authorized": True,
        "authorized_start_count": 1,
        "block_reason": "none",
        "blocked_start_count": 0,
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "confirmation_required": True,
        "confirmation_response": "confirmed",
        "confirmation_status": "required",
        "confirmation_verified": True,
        "course_count": 1,
        "courses": [
            {
                "authorized": True,
                "confirmation_response": "confirmed",
                "course_id": "cs101",
                "due": True,
                "enabled": True,
                "minutes_until_start": 0,
                "requires_confirmation": True,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "selected_class_time_index": 0,
                "stop_after_minutes": 75,
            }
        ],
        "due_count": 1,
        "ready_to_start": True,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "authorized",
    }
    assert captured.err == ""
    assert received == {
        "db_path": Path("schedule.sqlite"),
        "clock_kwargs": {"day_of_week": "monday", "local_time": "09:00"},
        "stored_courses": fake_store_payload,
        "archive_root": Path("archive-root"),
        "session_id": "session-001",
        "source_kind": "file",
        "clock": fake_clock,
        "enabled": True,
        "preflight_summary": preflight_summary,
        "confirmation_response": "confirmed",
        "response_summary": response_summary,
    }
    _assert_session_window_start_authorization_output_is_safe(
        captured.out,
        captured.err,
    )


def test_session_window_start_authorization_cli_requires_fixed_policy() -> None:
    payload: dict[str, object] = {
        "status": "authorized",
        "session_id": "session-001",
        "source_kind": "file",
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 1,
        "due_count": 1,
        "ready_to_start": True,
        "confirmation_required": True,
        "confirmation_status": "required",
        "confirmation_response": "custom free-form response",
        "confirmation_verified": True,
        "authorized": True,
        "authorized_start_count": 1,
        "blocked_start_count": 0,
        "block_reason": "none",
        "courses": [],
    }

    with pytest.raises(ValueError) as exc_info:
        cli._stored_session_window_start_authorization_safe_summary(payload)

    assert (
        str(exc_info.value)
        == "stored session window start authorization could not be built"
    )


def test_session_window_start_authorization_handler_stays_read_only() -> None:
    source = inspect.getsource(
        cli._run_session_window_start_authorization_from_store_local_command
    )

    assert "list_course_schedule_session_window_inputs" in source
    assert "ScheduledStartClock" in source
    assert "build_session_window_confirmation_preflight_summary" in source
    assert "build_session_window_confirmation_response_summary" in source
    assert "build_session_window_start_authorization_summary" in source
    for forbidden_fragment in (
        "_stored_session_window_confirmation_preflight_safe_summary",
        "_stored_session_window_confirmation_response_safe_summary",
        "load_course_schedule(",
        "load_course_schedule_read_only",
        "load_course_schedule_safe_summary",
        "list_course_schedule_safe_summaries",
        "list_course_schedule_due_list_inputs",
        "load_course_schedule_session_stop_input",
        "save_course_schedule",
        "initialize_course_schedule_store",
        "_create_schema",
        "ScheduleConfig",
        "CourseMetadata",
        "datetime",
        "now(",
        "sleep",
        "Timer(",
        "threading",
        "asyncio",
        "subprocess",
        "webbrowser",
        "requests",
        "httpx",
        "playwright",
        "selenium",
        "sounddevice",
        "faster_whisper",
        "mic_recording",
        "telegram",
        "desktop_notifier",
        "execute_archive",
        "archive_delete",
        ".open(",
        ".read_text(",
        ".write_text(",
        ".mkdir(",
        ".unlink(",
        ".remove(",
        ".rmdir(",
        "rmtree",
    ):
        assert forbidden_fragment not in source


def test_session_window_start_receipt_from_store_local_help_stays_lazy(
    monkeypatch,
) -> None:
    schedule_store_module = "async_scholar.schedule_store"
    scheduled_start_module = "async_scholar.scheduled_start"
    preflight_module = "async_scholar.session_window_confirmation_preflight"
    response_module = "async_scholar.session_window_confirmation_response"
    authorization_module = "async_scholar.session_window_start_authorization"
    receipt_module = "async_scholar.session_window_start_receipt"
    monkeypatch.delitem(sys.modules, schedule_store_module, raising=False)
    monkeypatch.delitem(sys.modules, scheduled_start_module, raising=False)
    monkeypatch.delitem(sys.modules, preflight_module, raising=False)
    monkeypatch.delitem(sys.modules, response_module, raising=False)
    monkeypatch.delitem(sys.modules, authorization_module, raising=False)
    monkeypatch.delitem(sys.modules, receipt_module, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-start-receipt-from-store-local",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert (
        "usage: async_scholar session-window-start-receipt-from-store-local"
        in result.stdout
    )
    assert "--db-path" in result.stdout
    assert "--archive-root" in result.stdout
    assert "--source-kind" in result.stdout
    assert "--clock-day-of-week" in result.stdout
    assert "--clock-local-time" in result.stdout
    assert "--confirmation-response" in result.stdout
    assert "confirmed" in result.stdout
    assert "declined" in result.stdout
    assert "metadata-only" in result.stdout
    assert schedule_store_module not in sys.modules
    assert scheduled_start_module not in sys.modules
    assert preflight_module not in sys.modules
    assert response_module not in sys.modules
    assert authorization_module not in sys.modules
    assert receipt_module not in sys.modules


def test_session_window_start_receipt_from_store_local_requires_metadata() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-start-receipt-from-store-local",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr == "stored session window start receipt could not be built\n"


def test_session_window_start_receipt_prints_confirmed_json_and_writes_runtime(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    archive_root = tmp_path / "archive"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    _write_private_course_schedule(db_path)
    (session_dir / "events.jsonl").write_text(
        "private event token secret auth profile payload",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-start-receipt-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
            "--confirmation-response",
            "confirmed",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    expected = {
        "authorized": True,
        "authorized_start_count": 1,
        "block_reason": "none",
        "blocked_start_count": 0,
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "confirmation_required": True,
        "confirmation_response": "confirmed",
        "confirmation_status": "required",
        "confirmation_verified": True,
        "course_count": 1,
        "due_count": 1,
        "ready_to_start": True,
        "receipt_kind": "stored_session_window_start_receipt",
        "runtime_record_written": True,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "authorized",
    }
    expected_line = json.dumps(expected, sort_keys=True, separators=(",", ":"))
    runtime_path = session_dir / "runtime.jsonl"
    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout == f"{expected_line}\n"
    assert runtime_path.read_text(encoding="utf-8") == f"{expected_line}\n"
    _assert_session_window_start_receipt_output_is_safe(
        result.stdout,
        result.stderr,
        runtime_path,
    )


def test_session_window_start_receipt_declined_does_not_write_runtime(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    archive_root = tmp_path / "archive"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-start-receipt-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
            "--confirmation-response",
            "declined",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert result.stderr == ""
    assert payload["status"] == "blocked"
    assert payload["authorized"] is False
    assert payload["runtime_record_written"] is False
    assert not (session_dir / "runtime.jsonl").exists()
    _assert_session_window_start_receipt_output_is_safe(
        result.stdout,
        result.stderr,
    )


def test_session_window_start_receipt_sanitizes_db_failure(
    tmp_path: Path,
) -> None:
    missing_db_path = tmp_path / "missing-token-secret-auth-profile.sqlite"
    archive_root = tmp_path / "archive"
    archive_root.mkdir()

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-start-receipt-from-store-local",
            "session-001",
            "--db-path",
            str(missing_db_path),
            "--archive-root",
            str(archive_root),
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
            "--confirmation-response",
            "confirmed",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "stored session window start receipt could not be built\n"
    assert not missing_db_path.exists()
    assert list(archive_root.iterdir()) == []
    for forbidden_fragment in (
        str(tmp_path),
        "missing-token",
        "secret",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_window_start_receipt_rejects_free_form_response() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-start-receipt-from-store-local",
            "session-001",
            "--db-path",
            "schedule.sqlite",
            "--archive-root",
            "archive",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
            "--confirmation-response",
            "yes please start this class",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "stored session window start receipt could not be built\n"


def test_session_window_start_receipt_misordered_uses_receipt_error() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--archive-root",
            "C:\\Users\\student\\token-secret-auth-profile",
            "session-window-start-receipt-from-store-local",
            "session-001",
            "--db-path",
            "C:\\Users\\student\\private.sqlite",
            "--confirmation-response",
            "confirmed",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "stored session window start receipt could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "token",
        "secret",
        "private.sqlite",
        "invalid choice",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_window_start_receipt_command_delegates_to_writer(
    capsys,
    monkeypatch,
) -> None:
    received: dict[str, object] = {}
    schedule_store_module = "async_scholar.schedule_store"
    scheduled_start_module = "async_scholar.scheduled_start"
    preflight_module = "async_scholar.session_window_confirmation_preflight"
    response_module = "async_scholar.session_window_confirmation_response"
    authorization_module = "async_scholar.session_window_start_authorization"
    receipt_module = "async_scholar.session_window_start_receipt"
    fake_schedule_store_module = types.ModuleType(schedule_store_module)
    fake_scheduled_start_module = types.ModuleType(scheduled_start_module)
    fake_preflight_module = types.ModuleType(preflight_module)
    fake_response_module = types.ModuleType(response_module)
    fake_authorization_module = types.ModuleType(authorization_module)
    fake_receipt_module = types.ModuleType(receipt_module)
    fake_store_payload = object()
    fake_clock = object()

    def fake_list(db_path: Path) -> object:
        received["db_path"] = db_path
        return fake_store_payload

    class FakeClock:
        def __new__(cls, **kwargs: object) -> object:
            received["clock_kwargs"] = kwargs
            return fake_clock

    def fake_build_preflight(
        stored_courses: object,
        archive_root: Path,
        session_id: str,
        source_kind: str,
        clock: object,
        *,
        enabled: bool,
    ) -> dict[str, object]:
        received["stored_courses"] = stored_courses
        received["archive_root"] = archive_root
        received["session_id"] = session_id
        received["source_kind"] = source_kind
        received["clock"] = clock
        received["enabled"] = enabled
        return {"preflight": "safe"}

    def fake_build_response(
        preflight_summary: dict[str, object],
        confirmation_response: str,
    ) -> dict[str, object]:
        received["preflight_summary"] = preflight_summary
        received["confirmation_response"] = confirmation_response
        return {"response": "safe"}

    def fake_build_authorization(
        response_summary: dict[str, object],
    ) -> dict[str, object]:
        received["response_summary"] = response_summary
        return {"authorization": "safe"}

    def fake_write_receipt(
        authorization_summary: dict[str, object],
        archive_root: Path,
    ) -> dict[str, object]:
        received["authorization_summary"] = authorization_summary
        received["receipt_archive_root"] = archive_root
        return {
            "status": "authorized",
            "session_id": "session-001",
            "runtime_record_written": True,
            "receipt_kind": "stored_session_window_start_receipt",
        }

    fake_schedule_store_module.list_course_schedule_session_window_inputs = fake_list
    fake_scheduled_start_module.ScheduledStartClock = FakeClock
    fake_preflight_module.build_session_window_confirmation_preflight_summary = (
        fake_build_preflight
    )
    fake_response_module.build_session_window_confirmation_response_summary = (
        fake_build_response
    )
    fake_authorization_module.build_session_window_start_authorization_summary = (
        fake_build_authorization
    )
    fake_receipt_module.write_stored_session_window_start_receipt = fake_write_receipt
    monkeypatch.setitem(sys.modules, schedule_store_module, fake_schedule_store_module)
    monkeypatch.setitem(
        sys.modules,
        scheduled_start_module,
        fake_scheduled_start_module,
    )
    monkeypatch.setitem(sys.modules, preflight_module, fake_preflight_module)
    monkeypatch.setitem(sys.modules, response_module, fake_response_module)
    monkeypatch.setitem(sys.modules, authorization_module, fake_authorization_module)
    monkeypatch.setitem(sys.modules, receipt_module, fake_receipt_module)

    exit_code = cli.main(
        [
            "session-window-start-receipt-from-store-local",
            "session-001",
            "--db-path",
            "schedule.sqlite",
            "--archive-root",
            "archive-root",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
            "--confirmation-response",
            "confirmed",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        '{"receipt_kind":"stored_session_window_start_receipt",'
        '"runtime_record_written":true,"session_id":"session-001",'
        '"status":"authorized"}\n'
    )
    assert captured.err == ""
    assert received == {
        "db_path": Path("schedule.sqlite"),
        "clock_kwargs": {"day_of_week": "monday", "local_time": "09:00"},
        "stored_courses": fake_store_payload,
        "archive_root": Path("archive-root"),
        "session_id": "session-001",
        "source_kind": "file",
        "clock": fake_clock,
        "enabled": True,
        "preflight_summary": {"preflight": "safe"},
        "confirmation_response": "confirmed",
        "response_summary": {"response": "safe"},
        "authorization_summary": {"authorization": "safe"},
        "receipt_archive_root": Path("archive-root"),
    }


def test_session_window_start_receipt_command_sanitizes_writer_failure(
    capsys,
    monkeypatch,
) -> None:
    schedule_store_module = "async_scholar.schedule_store"
    scheduled_start_module = "async_scholar.scheduled_start"
    preflight_module = "async_scholar.session_window_confirmation_preflight"
    response_module = "async_scholar.session_window_confirmation_response"
    authorization_module = "async_scholar.session_window_start_authorization"
    receipt_module = "async_scholar.session_window_start_receipt"
    fake_schedule_store_module = types.ModuleType(schedule_store_module)
    fake_scheduled_start_module = types.ModuleType(scheduled_start_module)
    fake_preflight_module = types.ModuleType(preflight_module)
    fake_response_module = types.ModuleType(response_module)
    fake_authorization_module = types.ModuleType(authorization_module)
    fake_receipt_module = types.ModuleType(receipt_module)

    class FakeClock:
        def __new__(cls, **kwargs: object) -> object:
            return object()

    fake_schedule_store_module.list_course_schedule_session_window_inputs = (
        lambda db_path: object()
    )
    fake_scheduled_start_module.ScheduledStartClock = FakeClock
    fake_preflight_module.build_session_window_confirmation_preflight_summary = (
        lambda *args, **kwargs: {"preflight": "safe"}
    )
    fake_response_module.build_session_window_confirmation_response_summary = (
        lambda *args, **kwargs: {"response": "safe"}
    )
    fake_authorization_module.build_session_window_start_authorization_summary = (
        lambda response_summary: {"authorization": "safe"}
    )

    def fake_write_receipt(
        authorization_summary: dict[str, object],
        archive_root: Path,
    ) -> dict[str, object]:
        raise ValueError("C:\\Users\\student\\token-secret-auth-profile")

    fake_receipt_module.write_stored_session_window_start_receipt = fake_write_receipt
    monkeypatch.setitem(sys.modules, schedule_store_module, fake_schedule_store_module)
    monkeypatch.setitem(
        sys.modules,
        scheduled_start_module,
        fake_scheduled_start_module,
    )
    monkeypatch.setitem(sys.modules, preflight_module, fake_preflight_module)
    monkeypatch.setitem(sys.modules, response_module, fake_response_module)
    monkeypatch.setitem(sys.modules, authorization_module, fake_authorization_module)
    monkeypatch.setitem(sys.modules, receipt_module, fake_receipt_module)

    exit_code = cli.main(
        [
            "session-window-start-receipt-from-store-local",
            "session-001",
            "--db-path",
            "schedule.sqlite",
            "--archive-root",
            "archive-root",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
            "--confirmation-response",
            "confirmed",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == "stored session window start receipt could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in captured.err


def test_session_window_start_receipt_handler_stays_thin() -> None:
    source = inspect.getsource(
        cli._run_session_window_start_receipt_from_store_local_command
    )

    assert "list_course_schedule_session_window_inputs" in source
    assert "ScheduledStartClock" in source
    assert "build_session_window_confirmation_preflight_summary" in source
    assert "build_session_window_confirmation_response_summary" in source
    assert "build_session_window_start_authorization_summary" in source
    assert "write_stored_session_window_start_receipt" in source
    for forbidden_fragment in (
        "_stored_session_window_start_authorization_safe_summary",
        "load_course_schedule(",
        "load_course_schedule_read_only",
        "load_course_schedule_safe_summary",
        "list_course_schedule_safe_summaries",
        "list_course_schedule_due_list_inputs",
        "load_course_schedule_session_stop_input",
        "save_course_schedule",
        "initialize_course_schedule_store",
        "_create_schema",
        "ScheduleConfig",
        "CourseMetadata",
        "datetime",
        "now(",
        "sleep",
        "Timer(",
        "threading",
        "asyncio",
        "subprocess",
        "webbrowser",
        "requests",
        "httpx",
        "playwright",
        "selenium",
        "sounddevice",
        "faster_whisper",
        "mic_recording",
        "telegram",
        "desktop_notifier",
        "execute_archive",
        "archive_delete",
        ".open(",
        ".read_text(",
        ".write_text(",
        ".mkdir(",
        ".unlink(",
        ".remove(",
        ".rmdir(",
        "rmtree",
        "autonomous",
        "academic_answer",
    ):
        assert forbidden_fragment not in source


def test_session_window_stop_receipt_from_store_local_help_stays_lazy(
    monkeypatch,
) -> None:
    schedule_store_module = "async_scholar.schedule_store"
    session_stop_module = "async_scholar.session_stop"
    receipt_module = "async_scholar.session_window_stop_receipt"
    monkeypatch.delitem(sys.modules, schedule_store_module, raising=False)
    monkeypatch.delitem(sys.modules, session_stop_module, raising=False)
    monkeypatch.delitem(sys.modules, receipt_module, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-stop-receipt-from-store-local",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar session-window-stop-receipt-from-store-local" in (
        result.stdout
    )
    assert "--db-path" in result.stdout
    assert "--archive-root" in result.stdout
    assert "--course-id" in result.stdout
    assert "--class-time-index" in result.stdout
    assert "--source-kind" in result.stdout
    assert "metadata-only" in result.stdout
    assert schedule_store_module not in sys.modules
    assert session_stop_module not in sys.modules
    assert receipt_module not in sys.modules


def test_session_window_stop_receipt_from_store_local_requires_metadata() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-stop-receipt-from-store-local",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr == "stored session window stop receipt could not be built\n"


def test_session_window_stop_receipt_prints_enabled_json_and_appends_runtime(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    archive_root = tmp_path / "archive"
    session_dir = archive_root / "session-001"
    runtime_path = session_dir / "runtime.jsonl"
    existing_line = '{"existing":true}\n'
    session_dir.mkdir(parents=True)
    runtime_path.write_text(existing_line, encoding="utf-8")
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-stop-receipt-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--archive-root",
            str(archive_root),
            "--course-id",
            "cs101",
            "--class-time-index",
            "0",
            "--source-kind",
            "file",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    expected = {
        "course_id": "cs101",
        "enabled": True,
        "receipt_kind": "stored_session_window_stop_receipt",
        "runtime_record_written": True,
        "scheduled_day_of_week": "monday",
        "scheduled_local_start_time": "09:00",
        "selected_class_time_index": 0,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "enabled",
        "stop_after_minutes": 75,
    }
    expected_line = json.dumps(expected, sort_keys=True, separators=(",", ":"))
    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout == f"{expected_line}\n"
    assert runtime_path.read_text(encoding="utf-8") == (
        f"{existing_line}{expected_line}\n"
    )
    _assert_session_window_stop_receipt_output_is_safe(
        result.stdout,
        result.stderr,
        runtime_path,
    )


def test_session_window_stop_receipt_disabled_does_not_write_or_create_archive(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    archive_root = tmp_path / "missing-archive"
    _write_private_course_schedule(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-stop-receipt-from-store-local",
            "session-001",
            "--db-path",
            str(db_path),
            "--archive-root",
            str(archive_root),
            "--course-id",
            "cs101",
            "--class-time-index",
            "0",
            "--source-kind",
            "mic",
            "--disabled",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert result.stderr == ""
    assert payload == {
        "course_id": "cs101",
        "enabled": False,
        "receipt_kind": "stored_session_window_stop_receipt",
        "runtime_record_written": False,
        "scheduled_day_of_week": "monday",
        "scheduled_local_start_time": "09:00",
        "selected_class_time_index": 0,
        "session_id": "session-001",
        "source_kind": "mic",
        "status": "disabled",
        "stop_after_minutes": 75,
    }
    assert not archive_root.exists()
    _assert_session_window_stop_receipt_output_is_safe(
        result.stdout,
        result.stderr,
    )


def test_session_window_stop_receipt_sanitizes_db_failure(
    tmp_path: Path,
) -> None:
    missing_db_path = tmp_path / "missing-token-secret-auth-profile.sqlite"
    archive_root = tmp_path / "archive"
    archive_root.mkdir()

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-stop-receipt-from-store-local",
            "session-001",
            "--db-path",
            str(missing_db_path),
            "--archive-root",
            str(archive_root),
            "--course-id",
            "cs101",
            "--class-time-index",
            "0",
            "--source-kind",
            "file",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "stored session window stop receipt could not be built\n"
    assert not missing_db_path.exists()
    assert list(archive_root.iterdir()) == []
    for forbidden_fragment in (
        str(tmp_path),
        "missing-token",
        "secret",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_window_stop_receipt_misordered_uses_receipt_error() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--archive-root",
            "C:\\Users\\student\\token-secret-auth-profile",
            "session-window-stop-receipt-from-store-local",
            "session-001",
            "--db-path",
            "C:\\Users\\student\\private.sqlite",
            "--course-id",
            "cs101",
            "--class-time-index",
            "0",
            "--source-kind",
            "file",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "stored session window stop receipt could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "token",
        "secret",
        "private.sqlite",
        "invalid choice",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_window_stop_receipt_command_delegates_to_stop_writer(
    capsys,
    monkeypatch,
) -> None:
    received: dict[str, object] = {}
    schedule_store_module = "async_scholar.schedule_store"
    session_stop_module = "async_scholar.session_stop"
    receipt_module = "async_scholar.session_window_stop_receipt"
    fake_schedule_store_module = types.ModuleType(schedule_store_module)
    fake_session_stop_module = types.ModuleType(session_stop_module)
    fake_receipt_module = types.ModuleType(receipt_module)
    fake_store_payload = object()

    def fake_load(
        db_path: Path,
        course_id: str,
        class_time_index: int,
    ) -> object:
        received["db_path"] = db_path
        received["course_id"] = course_id
        received["class_time_index"] = class_time_index
        return fake_store_payload

    def fake_build(
        stored_class_time: object,
        source_kind: str,
        *,
        enabled: bool,
    ) -> dict[str, object]:
        received["stored_class_time"] = stored_class_time
        received["source_kind"] = source_kind
        received["enabled"] = enabled
        return {"stop_preview": "safe"}

    def fake_write_receipt(
        stop_preview_summary: dict[str, object],
        archive_root: Path,
        session_id: str,
    ) -> dict[str, object]:
        received["stop_preview_summary"] = stop_preview_summary
        received["archive_root"] = archive_root
        received["session_id"] = session_id
        return {
            "receipt_kind": "stored_session_window_stop_receipt",
            "runtime_record_written": True,
            "session_id": "session-001",
            "status": "enabled",
        }

    fake_schedule_store_module.load_course_schedule_session_stop_input = fake_load
    fake_session_stop_module.build_session_stop_preview_from_store_input = fake_build
    fake_receipt_module.write_stored_session_window_stop_receipt = fake_write_receipt
    monkeypatch.setitem(sys.modules, schedule_store_module, fake_schedule_store_module)
    monkeypatch.setitem(sys.modules, session_stop_module, fake_session_stop_module)
    monkeypatch.setitem(sys.modules, receipt_module, fake_receipt_module)

    exit_code = cli.main(
        [
            "session-window-stop-receipt-from-store-local",
            "session-001",
            "--db-path",
            "schedule.sqlite",
            "--archive-root",
            "archive-root",
            "--course-id",
            "cs101",
            "--class-time-index",
            "0",
            "--source-kind",
            "file",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        '{"receipt_kind":"stored_session_window_stop_receipt",'
        '"runtime_record_written":true,"session_id":"session-001",'
        '"status":"enabled"}\n'
    )
    assert captured.err == ""
    assert received == {
        "db_path": Path("schedule.sqlite"),
        "course_id": "cs101",
        "class_time_index": 0,
        "stored_class_time": fake_store_payload,
        "source_kind": "file",
        "enabled": True,
        "stop_preview_summary": {"stop_preview": "safe"},
        "archive_root": Path("archive-root"),
        "session_id": "session-001",
    }


def test_session_window_stop_receipt_command_sanitizes_writer_failure(
    capsys,
    monkeypatch,
) -> None:
    schedule_store_module = "async_scholar.schedule_store"
    session_stop_module = "async_scholar.session_stop"
    receipt_module = "async_scholar.session_window_stop_receipt"
    fake_schedule_store_module = types.ModuleType(schedule_store_module)
    fake_session_stop_module = types.ModuleType(session_stop_module)
    fake_receipt_module = types.ModuleType(receipt_module)

    fake_schedule_store_module.load_course_schedule_session_stop_input = lambda *args: (
        object()
    )
    fake_session_stop_module.build_session_stop_preview_from_store_input = (
        lambda *args, **kwargs: {"stop_preview": "safe"}
    )

    def fake_write_receipt(
        stop_preview_summary: dict[str, object],
        archive_root: Path,
        session_id: str,
    ) -> dict[str, object]:
        raise ValueError("C:\\Users\\student\\token-secret-auth-profile")

    fake_receipt_module.write_stored_session_window_stop_receipt = fake_write_receipt
    monkeypatch.setitem(sys.modules, schedule_store_module, fake_schedule_store_module)
    monkeypatch.setitem(sys.modules, session_stop_module, fake_session_stop_module)
    monkeypatch.setitem(sys.modules, receipt_module, fake_receipt_module)

    exit_code = cli.main(
        [
            "session-window-stop-receipt-from-store-local",
            "session-001",
            "--db-path",
            "schedule.sqlite",
            "--archive-root",
            "archive-root",
            "--course-id",
            "cs101",
            "--class-time-index",
            "0",
            "--source-kind",
            "file",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == "stored session window stop receipt could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in captured.err


def test_session_window_runtime_summary_local_help_stays_lazy(
    monkeypatch,
) -> None:
    summary_module = "async_scholar.session_window_runtime_summary"
    monkeypatch.delitem(sys.modules, summary_module, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-runtime-summary-local",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar session-window-runtime-summary-local" in (
        result.stdout
    )
    assert "--archive-root" in result.stdout
    assert "read-only" in result.stdout
    assert "runtime" in result.stdout
    assert summary_module not in sys.modules


def test_session_window_runtime_summary_local_requires_metadata() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-runtime-summary-local",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr == "stored session window runtime summary could not be built\n"


def test_session_window_runtime_summary_prints_compact_json(
    tmp_path: Path,
) -> None:
    archive_root = tmp_path / "archive"
    session_dir = archive_root / "session-001"
    runtime_path = session_dir / "runtime.jsonl"
    session_dir.mkdir(parents=True)
    start_receipt = _session_window_runtime_start_receipt()
    runtime_path.write_text(
        json.dumps(start_receipt, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-runtime-summary-local",
            "session-001",
            "--archive-root",
            str(archive_root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    expected = {
        "summary_kind": "stored_session_window_runtime_summary",
        "session_id": "session-001",
        "runtime_record_count": 1,
        "start_receipt_count": 1,
        "stop_receipt_count": 0,
        "lifecycle_status": "started",
        "session_active": True,
        "session_stopped": False,
        "last_receipt_kind": "stored_session_window_start_receipt",
        "last_source_kind": "file",
    }
    expected_line = json.dumps(expected, sort_keys=True, separators=(",", ":"))
    assert result.returncode == 0
    assert result.stdout == f"{expected_line}\n"
    assert result.stderr == ""
    _assert_session_window_runtime_summary_output_is_safe(
        result.stdout,
        result.stderr,
    )


def test_session_window_runtime_summary_sanitizes_runtime_failure(
    tmp_path: Path,
) -> None:
    archive_root = tmp_path / "archive-token-secret-auth-profile"
    session_dir = archive_root / "session-001"
    runtime_path = session_dir / "runtime.jsonl"
    session_dir.mkdir(parents=True)
    private_receipt = _session_window_runtime_start_receipt(
        private_path=str(tmp_path),
    )
    runtime_path.write_text(
        json.dumps(private_receipt, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-runtime-summary-local",
            "session-001",
            "--archive-root",
            str(archive_root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "stored session window runtime summary could not be built\n"
    for forbidden_fragment in (
        str(tmp_path),
        "token",
        "secret",
        "auth",
        "profile",
        "private_path",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_window_runtime_summary_misordered_uses_summary_error() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--archive-root",
            "C:\\Users\\student\\token-secret-auth-profile",
            "session-window-runtime-summary-local",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "stored session window runtime summary could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "token",
        "secret",
        "invalid choice",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_window_runtime_summary_command_delegates_to_reader(
    capsys,
    monkeypatch,
) -> None:
    received: dict[str, object] = {}
    summary_module = "async_scholar.session_window_runtime_summary"
    fake_summary_module = types.ModuleType(summary_module)

    def fake_build(archive_root: Path, session_id: str) -> dict[str, object]:
        received["archive_root"] = archive_root
        received["session_id"] = session_id
        return {
            "summary_kind": "stored_session_window_runtime_summary",
            "session_id": "session-001",
            "runtime_record_count": 0,
            "start_receipt_count": 0,
            "stop_receipt_count": 0,
            "lifecycle_status": "not_started",
            "session_active": False,
            "session_stopped": False,
            "last_receipt_kind": "none",
            "last_source_kind": "none",
        }

    fake_summary_module.build_stored_session_window_runtime_summary = fake_build
    monkeypatch.setitem(sys.modules, summary_module, fake_summary_module)

    exit_code = cli.main(
        [
            "session-window-runtime-summary-local",
            "session-001",
            "--archive-root",
            "archive-root",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        '{"last_receipt_kind":"none","last_source_kind":"none",'
        '"lifecycle_status":"not_started","runtime_record_count":0,'
        '"session_active":false,"session_id":"session-001",'
        '"session_stopped":false,"start_receipt_count":0,'
        '"stop_receipt_count":0,'
        '"summary_kind":"stored_session_window_runtime_summary"}\n'
    )
    assert captured.err == ""
    assert received == {
        "archive_root": Path("archive-root"),
        "session_id": "session-001",
    }


def test_session_window_runtime_summary_command_sanitizes_reader_failure(
    capsys,
    monkeypatch,
) -> None:
    summary_module = "async_scholar.session_window_runtime_summary"
    fake_summary_module = types.ModuleType(summary_module)

    def fake_build(archive_root: Path, session_id: str) -> dict[str, object]:
        raise ValueError("C:\\Users\\student\\token-secret-auth-profile")

    fake_summary_module.build_stored_session_window_runtime_summary = fake_build
    monkeypatch.setitem(sys.modules, summary_module, fake_summary_module)

    exit_code = cli.main(
        [
            "session-window-runtime-summary-local",
            "session-001",
            "--archive-root",
            "archive-root",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == "stored session window runtime summary could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in captured.err


def test_session_window_recovery_decision_local_help_stays_lazy(
    monkeypatch,
) -> None:
    decision_module = "async_scholar.session_window_recovery_decision"
    monkeypatch.delitem(sys.modules, decision_module, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-recovery-decision-local",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar session-window-recovery-decision-local" in (
        result.stdout
    )
    assert "--archive-root" in result.stdout
    assert "read-only" in result.stdout
    assert "recovery decision" in result.stdout
    assert decision_module not in sys.modules


def test_session_window_recovery_decision_local_requires_metadata() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-recovery-decision-local",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert (
        result.stderr == "stored session window recovery decision could not be built\n"
    )


def test_session_window_recovery_decision_prints_compact_json(
    tmp_path: Path,
) -> None:
    archive_root = tmp_path / "archive"
    session_dir = archive_root / "session-001"
    runtime_path = session_dir / "runtime.jsonl"
    session_dir.mkdir(parents=True)
    start_receipt = _session_window_runtime_start_receipt()
    runtime_path.write_text(
        json.dumps(start_receipt, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-recovery-decision-local",
            "session-001",
            "--archive-root",
            str(archive_root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    expected = {
        "decision_kind": "stored_session_window_recovery_decision",
        "session_id": "session-001",
        "runtime_lifecycle_status": "started",
        "runtime_record_count": 1,
        "start_receipt_count": 1,
        "stop_receipt_count": 0,
        "session_active": True,
        "session_stopped": False,
        "archive_recovery_status": "empty",
        "archive_existing_count": 0,
        "archive_missing_count": 6,
        "recovery_decision": "inspect_active_session",
        "manual_review_required": True,
    }
    expected_line = json.dumps(expected, sort_keys=True, separators=(",", ":"))
    assert result.returncode == 0
    assert result.stdout == f"{expected_line}\n"
    assert result.stderr == ""
    _assert_session_window_recovery_decision_output_is_safe(
        result.stdout,
        result.stderr,
    )


def test_session_window_recovery_decision_sanitizes_build_failure(
    tmp_path: Path,
) -> None:
    archive_root = tmp_path / "archive-token-secret-auth-profile"
    session_dir = archive_root / "session-001"
    runtime_path = session_dir / "runtime.jsonl"
    session_dir.mkdir(parents=True)
    private_receipt = _session_window_runtime_start_receipt(
        private_path=str(tmp_path),
    )
    runtime_path.write_text(
        json.dumps(private_receipt, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-recovery-decision-local",
            "session-001",
            "--archive-root",
            str(archive_root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert (
        result.stderr == "stored session window recovery decision could not be built\n"
    )
    for forbidden_fragment in (
        str(tmp_path),
        "token",
        "secret",
        "auth",
        "profile",
        "private_path",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_window_recovery_decision_misordered_uses_decision_error() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--archive-root",
            "C:\\Users\\student\\token-secret-auth-profile",
            "session-window-recovery-decision-local",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert (
        result.stderr == "stored session window recovery decision could not be built\n"
    )
    for forbidden_fragment in (
        "C:\\Users",
        "token",
        "secret",
        "invalid choice",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_window_recovery_decision_command_delegates_to_builder(
    capsys,
    monkeypatch,
) -> None:
    received: dict[str, object] = {}
    decision_module = "async_scholar.session_window_recovery_decision"
    fake_decision_module = types.ModuleType(decision_module)

    def fake_build(archive_root: Path, session_id: str) -> dict[str, object]:
        received["archive_root"] = archive_root
        received["session_id"] = session_id
        return {
            "decision_kind": "stored_session_window_recovery_decision",
            "session_id": "session-001",
            "runtime_lifecycle_status": "not_started",
            "runtime_record_count": 0,
            "start_receipt_count": 0,
            "stop_receipt_count": 0,
            "session_active": False,
            "session_stopped": False,
            "archive_recovery_status": "empty",
            "archive_existing_count": 0,
            "archive_missing_count": 6,
            "recovery_decision": "no_action",
            "manual_review_required": False,
        }

    fake_decision_module.build_stored_session_window_recovery_decision = fake_build
    monkeypatch.setitem(sys.modules, decision_module, fake_decision_module)

    exit_code = cli.main(
        [
            "session-window-recovery-decision-local",
            "session-001",
            "--archive-root",
            "archive-root",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        '{"archive_existing_count":0,"archive_missing_count":6,'
        '"archive_recovery_status":"empty",'
        '"decision_kind":"stored_session_window_recovery_decision",'
        '"manual_review_required":false,"recovery_decision":"no_action",'
        '"runtime_lifecycle_status":"not_started","runtime_record_count":0,'
        '"session_active":false,"session_id":"session-001",'
        '"session_stopped":false,"start_receipt_count":0,'
        '"stop_receipt_count":0}\n'
    )
    assert captured.err == ""
    assert received == {
        "archive_root": Path("archive-root"),
        "session_id": "session-001",
    }


def test_session_window_recovery_decision_command_sanitizes_builder_failure(
    capsys,
    monkeypatch,
) -> None:
    decision_module = "async_scholar.session_window_recovery_decision"
    fake_decision_module = types.ModuleType(decision_module)

    def fake_build(archive_root: Path, session_id: str) -> dict[str, object]:
        raise ValueError("C:\\Users\\student\\token-secret-auth-profile")

    fake_decision_module.build_stored_session_window_recovery_decision = fake_build
    monkeypatch.setitem(sys.modules, decision_module, fake_decision_module)

    exit_code = cli.main(
        [
            "session-window-recovery-decision-local",
            "session-001",
            "--archive-root",
            "archive-root",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert (
        captured.err == "stored session window recovery decision could not be built\n"
    )
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in captured.err


def test_session_window_recovery_review_local_help_stays_lazy(
    monkeypatch,
) -> None:
    review_module = "async_scholar.session_window_recovery_review"
    monkeypatch.delitem(sys.modules, review_module, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-recovery-review-local",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar session-window-recovery-review-local" in (
        result.stdout
    )
    assert "--archive-root" in result.stdout
    assert "read-only" in result.stdout
    assert "recovery review" in result.stdout
    assert review_module not in sys.modules


def test_session_window_recovery_review_local_requires_metadata() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-recovery-review-local",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr == "stored session window recovery review could not be built\n"


def test_session_window_recovery_review_prints_compact_json(
    tmp_path: Path,
) -> None:
    archive_root = tmp_path / "archive"
    session_dir = archive_root / "session-001"
    runtime_path = session_dir / "runtime.jsonl"
    session_dir.mkdir(parents=True)
    start_receipt = _session_window_runtime_start_receipt()
    runtime_path.write_text(
        json.dumps(start_receipt, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-recovery-review-local",
            "session-001",
            "--archive-root",
            str(archive_root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    expected = {
        "review_kind": "stored_session_window_recovery_review",
        "session_id": "session-001",
        "runtime_lifecycle_status": "started",
        "archive_recovery_status": "empty",
        "archive_existing_count": 0,
        "archive_missing_count": 6,
        "recovery_decision": "inspect_active_session",
        "manual_review_required": True,
        "review_status": "required",
        "review_reason": "active_session_runtime",
        "safe_next_review_action": "inspect_runtime_metadata",
    }
    expected_line = json.dumps(expected, sort_keys=True, separators=(",", ":"))
    assert result.returncode == 0
    assert result.stdout == f"{expected_line}\n"
    assert result.stderr == ""
    _assert_session_window_recovery_decision_output_is_safe(
        result.stdout,
        result.stderr,
    )


def test_session_window_recovery_review_sanitizes_build_failure(
    tmp_path: Path,
) -> None:
    archive_root = tmp_path / "archive-token-secret-auth-profile"
    session_dir = archive_root / "session-001"
    runtime_path = session_dir / "runtime.jsonl"
    session_dir.mkdir(parents=True)
    private_receipt = _session_window_runtime_start_receipt(
        private_path=str(tmp_path),
    )
    runtime_path.write_text(
        json.dumps(private_receipt, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "session-window-recovery-review-local",
            "session-001",
            "--archive-root",
            str(archive_root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "stored session window recovery review could not be built\n"
    for forbidden_fragment in (
        str(tmp_path),
        "token",
        "secret",
        "auth",
        "profile",
        "private_path",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_window_recovery_review_misordered_uses_review_error() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--archive-root",
            "C:\\Users\\student\\token-secret-auth-profile",
            "session-window-recovery-review-local",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "stored session window recovery review could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "token",
        "secret",
        "invalid choice",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_session_window_recovery_review_command_delegates_to_builder(
    capsys,
    monkeypatch,
) -> None:
    received: dict[str, object] = {}
    review_module = "async_scholar.session_window_recovery_review"
    fake_review_module = types.ModuleType(review_module)

    def fake_build(archive_root: Path, session_id: str) -> dict[str, object]:
        received["archive_root"] = archive_root
        received["session_id"] = session_id
        return {
            "review_kind": "stored_session_window_recovery_review",
            "session_id": "session-001",
            "runtime_lifecycle_status": "not_started",
            "archive_recovery_status": "empty",
            "archive_existing_count": 0,
            "archive_missing_count": 6,
            "recovery_decision": "no_action",
            "manual_review_required": False,
            "review_status": "not_required",
            "review_reason": "none",
            "safe_next_review_action": "leave_archive_unchanged",
        }

    fake_review_module.build_stored_session_window_recovery_review = fake_build
    monkeypatch.setitem(sys.modules, review_module, fake_review_module)

    exit_code = cli.main(
        [
            "session-window-recovery-review-local",
            "session-001",
            "--archive-root",
            "archive-root",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        '{"archive_existing_count":0,"archive_missing_count":6,'
        '"archive_recovery_status":"empty","manual_review_required":false,'
        '"recovery_decision":"no_action",'
        '"review_kind":"stored_session_window_recovery_review",'
        '"review_reason":"none","review_status":"not_required",'
        '"runtime_lifecycle_status":"not_started",'
        '"safe_next_review_action":"leave_archive_unchanged",'
        '"session_id":"session-001"}\n'
    )
    assert captured.err == ""
    assert received == {
        "archive_root": Path("archive-root"),
        "session_id": "session-001",
    }


def test_session_window_recovery_review_command_sanitizes_builder_failure(
    capsys,
    monkeypatch,
) -> None:
    review_module = "async_scholar.session_window_recovery_review"
    fake_review_module = types.ModuleType(review_module)

    def fake_build(archive_root: Path, session_id: str) -> dict[str, object]:
        raise ValueError("C:\\Users\\student\\token-secret-auth-profile")

    fake_review_module.build_stored_session_window_recovery_review = fake_build
    monkeypatch.setitem(sys.modules, review_module, fake_review_module)

    exit_code = cli.main(
        [
            "session-window-recovery-review-local",
            "session-001",
            "--archive-root",
            "archive-root",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == "stored session window recovery review could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in captured.err


def test_session_window_recovery_decision_handler_stays_thin() -> None:
    source = inspect.getsource(cli._run_session_window_recovery_decision_local_command)

    assert "build_stored_session_window_recovery_decision" in source
    for forbidden_fragment in (
        "list_course_schedule_session_window_inputs",
        "load_course_schedule",
        "save_course_schedule",
        "initialize_course_schedule_store",
        "_create_schema",
        "ScheduleConfig",
        "CourseMetadata",
        "ScheduledStartClock",
        "build_session_window_confirmation",
        "build_session_window_start_authorization",
        "write_stored_session_window_start_receipt",
        "write_stored_session_window_stop_receipt",
        "datetime",
        "now(",
        "sleep",
        "Timer(",
        "threading",
        "asyncio",
        "subprocess",
        "webbrowser",
        "requests",
        "httpx",
        "playwright",
        "selenium",
        "sounddevice",
        "faster_whisper",
        "mic_recording",
        "telegram",
        "desktop_notifier",
        "alert_dispatch",
        "execute_archive",
        "archive_export",
        "archive_delete",
        ".open(",
        ".read_text(",
        ".write_text(",
        ".mkdir(",
        ".unlink(",
        ".remove(",
        ".rmdir(",
        "rmtree",
        "autonomous",
        "academic_answer",
    ):
        assert forbidden_fragment not in source


def test_session_window_recovery_review_handler_stays_thin() -> None:
    source = inspect.getsource(cli._run_session_window_recovery_review_local_command)

    assert "build_stored_session_window_recovery_review" in source
    for forbidden_fragment in (
        "build_stored_session_window_recovery_decision",
        "build_stored_session_window_runtime_summary",
        "build_crash_recovery_session_preflight",
        "list_course_schedule_session_window_inputs",
        "load_course_schedule",
        "save_course_schedule",
        "initialize_course_schedule_store",
        "_create_schema",
        "ScheduleConfig",
        "CourseMetadata",
        "ScheduledStartClock",
        "build_session_window_confirmation",
        "build_session_window_start_authorization",
        "write_stored_session_window_start_receipt",
        "write_stored_session_window_stop_receipt",
        "datetime",
        "now(",
        "sleep",
        "Timer(",
        "threading",
        "asyncio",
        "subprocess",
        "webbrowser",
        "requests",
        "httpx",
        "playwright",
        "selenium",
        "sounddevice",
        "faster_whisper",
        "mic_recording",
        "telegram",
        "desktop_notifier",
        "alert_dispatch",
        "execute_archive",
        "archive_export",
        "archive_delete",
        "participation",
        "academic_answer",
        "gate d",
        "product promise",
    ):
        assert forbidden_fragment not in source


def test_session_window_runtime_summary_handler_stays_thin() -> None:
    source = inspect.getsource(cli._run_session_window_runtime_summary_local_command)

    assert "build_stored_session_window_runtime_summary" in source
    for forbidden_fragment in (
        "list_course_schedule_session_window_inputs",
        "load_course_schedule",
        "save_course_schedule",
        "initialize_course_schedule_store",
        "_create_schema",
        "ScheduleConfig",
        "CourseMetadata",
        "ScheduledStartClock",
        "build_session_window_confirmation",
        "build_session_window_start_authorization",
        "write_stored_session_window_start_receipt",
        "write_stored_session_window_stop_receipt",
        "datetime",
        "now(",
        "sleep",
        "Timer(",
        "threading",
        "asyncio",
        "subprocess",
        "webbrowser",
        "requests",
        "httpx",
        "playwright",
        "selenium",
        "sounddevice",
        "faster_whisper",
        "mic_recording",
        "telegram",
        "desktop_notifier",
        "alert_dispatch",
        "execute_archive",
        "archive_export",
        "archive_delete",
        ".open(",
        ".read_text(",
        ".write_text(",
        ".mkdir(",
        ".unlink(",
        ".remove(",
        ".rmdir(",
        "rmtree",
        "autonomous",
        "academic_answer",
    ):
        assert forbidden_fragment not in source


def test_session_window_stop_receipt_handler_stays_thin() -> None:
    source = inspect.getsource(
        cli._run_session_window_stop_receipt_from_store_local_command
    )

    assert "load_course_schedule_session_stop_input" in source
    assert "build_session_stop_preview_from_store_input" in source
    assert "write_stored_session_window_stop_receipt" in source
    for forbidden_fragment in (
        "list_course_schedule_session_window_inputs",
        "list_course_schedule_due_list_inputs",
        "load_course_schedule(",
        "load_course_schedule_read_only",
        "load_course_schedule_safe_summary",
        "list_course_schedule_safe_summaries",
        "save_course_schedule",
        "initialize_course_schedule_store",
        "_create_schema",
        "ScheduleConfig",
        "CourseMetadata",
        "ScheduledStartClock",
        "build_session_window_confirmation_preflight_summary",
        "build_session_window_confirmation_response_summary",
        "build_session_window_start_authorization_summary",
        "write_stored_session_window_start_receipt",
        "datetime",
        "now(",
        "sleep",
        "Timer(",
        "threading",
        "asyncio",
        "subprocess",
        "webbrowser",
        "requests",
        "httpx",
        "playwright",
        "selenium",
        "sounddevice",
        "faster_whisper",
        "mic_recording",
        "telegram",
        "desktop_notifier",
        "alert_dispatch",
        "execute_archive",
        "archive_export",
        "archive_delete",
        ".open(",
        ".read_text(",
        ".write_text(",
        ".mkdir(",
        ".unlink(",
        ".remove(",
        ".rmdir(",
        "rmtree",
        "autonomous",
        "academic_answer",
    ):
        assert forbidden_fragment not in source


def _assert_session_window_start_authorization_output_is_safe(
    stdout: str,
    stderr: str,
) -> None:
    combined_output = f"{stdout}\n{stderr}".lower()
    for forbidden_fragment in (
        "result_kind",
        "alert_preview",
        "alert_preview_count",
        "archive_",
        "title",
        "meeting",
        "meet.example",
        "timezone",
        "duration",
        "confidential",
        "instructor",
        "dr.",
        "lecture",
        "lab",
        "c:\\",
        "\\\\server",
        "/users",
        str(Path.home()).lower(),
        "token",
        "secret",
        "auth state",
        "auth_state",
        "auth-profile",
        "cookie",
        "profile",
        "transcript",
        "audio",
        "browser",
        "session_dir",
        "artifacts",
        "filename",
        "events.jsonl",
        "alerts.log",
        "reviewer.md",
        "runtime.jsonl",
        "benchmark-report.json",
        "sqlite",
        "traceback",
        "live delivery",
        "live-delivery",
        "live_delivery",
        "dispatch",
        "notification",
        "payload",
        "body",
        "target",
        "scheduler execution",
        "gate d",
        "product promise",
    ):
        assert forbidden_fragment not in combined_output


def _assert_session_window_start_receipt_output_is_safe(
    stdout: str,
    stderr: str,
    runtime_path: Path | None = None,
) -> None:
    combined_output = f"{stdout}\n{stderr}".lower()
    if runtime_path is not None:
        combined_output += runtime_path.read_text(encoding="utf-8").lower()
    for forbidden_fragment in (
        "result_kind",
        "alert_preview",
        "alert_preview_count",
        "archive_",
        "db_path",
        "title",
        "meeting",
        "meet.example",
        "timezone",
        "duration",
        "confidential",
        "instructor",
        "dr.",
        "lecture",
        "lab",
        "c:\\",
        "\\\\server",
        "/users",
        str(Path.home()).lower(),
        "token",
        "secret",
        "auth state",
        "auth_state",
        "auth-profile",
        "cookie",
        "profile",
        "transcript",
        "audio",
        "browser",
        "session_dir",
        "artifacts",
        "filename",
        "events.jsonl",
        "alerts.log",
        "reviewer.md",
        "runtime.jsonl",
        "benchmark-report.json",
        "sqlite",
        "traceback",
        "live delivery",
        "live-delivery",
        "live_delivery",
        "dispatch",
        "notification",
        "payload",
        "body",
        "target",
        "scheduler execution",
        "gate d",
        "product promise",
    ):
        assert forbidden_fragment not in combined_output


def _assert_session_window_stop_receipt_output_is_safe(
    stdout: str,
    stderr: str,
    runtime_path: Path | None = None,
) -> None:
    combined_output = f"{stdout}\n{stderr}".lower()
    if runtime_path is not None:
        combined_output += runtime_path.read_text(encoding="utf-8").lower()
    for forbidden_fragment in (
        "result_kind",
        "alert_preview",
        "alert_preview_count",
        "archive_",
        "db_path",
        "title",
        "meeting",
        "meet.example",
        "timezone",
        "duration",
        "confidential",
        "instructor",
        "dr.",
        "lecture",
        "lab",
        "c:\\",
        "\\\\server",
        "/users",
        str(Path.home()).lower(),
        "token",
        "secret",
        "auth state",
        "auth_state",
        "auth-profile",
        "cookie",
        "profile",
        "transcript",
        "audio",
        "browser",
        "session_dir",
        "artifacts",
        "filename",
        "events.jsonl",
        "alerts.log",
        "reviewer.md",
        "runtime.jsonl",
        "benchmark-report.json",
        "sqlite",
        "traceback",
        "live delivery",
        "live-delivery",
        "live_delivery",
        "dispatch",
        "notification",
        "payload",
        "body",
        "target",
        "scheduler execution",
        "gate d",
        "product promise",
    ):
        assert forbidden_fragment not in combined_output


def _assert_session_window_runtime_summary_output_is_safe(
    stdout: str,
    stderr: str,
) -> None:
    combined_output = f"{stdout}\n{stderr}".lower()
    for forbidden_fragment in (
        "result_kind",
        "alert_preview",
        "alert_preview_count",
        "archive_",
        "db_path",
        "course_id",
        "clock",
        "scheduled",
        "title",
        "meeting",
        "meet.example",
        "timezone",
        "duration",
        "confidential",
        "instructor",
        "dr.",
        "lecture",
        "lab",
        "c:\\",
        "\\\\server",
        "/users",
        str(Path.home()).lower(),
        "token",
        "secret",
        "auth state",
        "auth_state",
        "auth-profile",
        "cookie",
        "profile",
        "transcript",
        "audio",
        "browser",
        "session_dir",
        "artifacts",
        "filename",
        "events.jsonl",
        "alerts.log",
        "reviewer.md",
        "runtime.jsonl",
        "benchmark-report.json",
        "sqlite",
        "traceback",
        "live delivery",
        "live-delivery",
        "live_delivery",
        "dispatch",
        "notification",
        "payload",
        "body",
        "target",
        "scheduler execution",
        "gate d",
        "product promise",
    ):
        assert forbidden_fragment not in combined_output


def _assert_session_window_recovery_decision_output_is_safe(
    stdout: str,
    stderr: str,
) -> None:
    combined_output = f"{stdout}\n{stderr}".lower()
    for forbidden_fragment in (
        "result_kind",
        "alert_preview",
        "alert_preview_count",
        "db_path",
        "course_id",
        "clock",
        "scheduled",
        "title",
        "meeting",
        "meet.example",
        "timezone",
        "duration",
        "confidential",
        "instructor",
        "dr.",
        "lecture",
        "lab",
        "c:\\",
        "\\\\server",
        "/users",
        str(Path.home()).lower(),
        "token",
        "secret",
        "auth state",
        "auth_state",
        "auth-profile",
        "cookie",
        "profile",
        "transcript",
        "audio",
        "browser",
        "session_dir",
        "artifacts",
        "filename",
        "events.jsonl",
        "alerts.log",
        "reviewer.md",
        "runtime.jsonl",
        "benchmark-report.json",
        "sqlite",
        "traceback",
        "live delivery",
        "live-delivery",
        "live_delivery",
        "dispatch",
        "notification",
        "payload",
        "body",
        "target",
        "scheduler execution",
        "gate d",
        "product promise",
    ):
        assert forbidden_fragment not in combined_output


def _session_window_runtime_start_receipt(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "receipt_kind": "stored_session_window_start_receipt",
        "status": "authorized",
        "session_id": "session-001",
        "source_kind": "file",
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 1,
        "due_count": 1,
        "ready_to_start": True,
        "confirmation_required": True,
        "confirmation_status": "required",
        "confirmation_response": "confirmed",
        "confirmation_verified": True,
        "authorized": True,
        "authorized_start_count": 1,
        "blocked_start_count": 0,
        "block_reason": "none",
        "runtime_record_written": True,
    }
    payload.update(overrides)
    return payload


def _assert_session_stop_preview_output_is_safe(
    stdout: str,
    stderr: str,
) -> None:
    combined_output = f"{stdout}\n{stderr}".lower()
    for forbidden_fragment in (
        "result_kind",
        "title",
        "meeting",
        "meet.example",
        "timezone",
        "duration",
        "confidential",
        "instructor",
        "dr.",
        "lecture",
        "lab",
        "c:\\",
        "\\\\server",
        "/users",
        str(Path.home()).lower(),
        "token",
        "secret",
        "auth",
        "cookie",
        "profile",
        "transcript",
        "audio",
        "browser",
        "artifact",
        "sqlite",
        "traceback",
        "live",
        "delivery",
        "scheduler execution",
        "gate d",
        "product promise",
    ):
        assert forbidden_fragment not in combined_output


def _assert_session_window_plan_output_is_safe(
    stdout: str,
    stderr: str,
) -> None:
    combined_output = f"{stdout}\n{stderr}".lower()
    for forbidden_fragment in (
        "result_kind",
        "title",
        "meeting",
        "meet.example",
        "timezone",
        "duration",
        "confidential",
        "instructor",
        "dr.",
        "lecture",
        "lab",
        "c:\\",
        "\\\\server",
        "/users",
        str(Path.home()).lower(),
        "token",
        "secret",
        "auth",
        "cookie",
        "profile",
        "transcript",
        "audio",
        "browser",
        "artifact",
        "sqlite",
        "traceback",
        "live",
        "delivery",
        "scheduler execution",
        "gate d",
        "product promise",
    ):
        assert forbidden_fragment not in combined_output


def _assert_session_window_archive_preflight_output_is_safe(
    stdout: str,
    stderr: str,
) -> None:
    combined_output = f"{stdout}\n{stderr}".lower()
    for forbidden_fragment in (
        "result_kind",
        "title",
        "meeting",
        "meet.example",
        "timezone",
        "duration",
        "confidential",
        "instructor",
        "dr.",
        "lecture",
        "lab",
        "c:\\",
        "\\\\server",
        "/users",
        str(Path.home()).lower(),
        "token",
        "secret",
        "auth",
        "cookie",
        "profile",
        "transcript",
        "audio",
        "browser",
        "session_dir",
        "artifacts",
        "filename",
        "events.jsonl",
        "alerts.log",
        "reviewer.md",
        "runtime.jsonl",
        "benchmark-report.json",
        "sqlite",
        "traceback",
        "live",
        "delivery",
        "scheduler execution",
        "gate d",
        "product promise",
    ):
        assert forbidden_fragment not in combined_output


def _assert_session_window_alert_preview_output_is_safe(
    stdout: str,
    stderr: str,
) -> None:
    combined_output = f"{stdout}\n{stderr}".lower()
    for forbidden_fragment in (
        "result_kind",
        "title",
        "meeting",
        "meet.example",
        "timezone",
        "duration",
        "confidential",
        "instructor",
        "dr.",
        "lecture",
        "lab",
        "c:\\",
        "\\\\server",
        "/users",
        str(Path.home()).lower(),
        "token",
        "secret",
        "auth",
        "cookie",
        "profile",
        "transcript",
        "audio",
        "browser",
        "artifact",
        "sqlite",
        "traceback",
        "live delivery",
        "live-delivery",
        "live_delivery",
        "dispatch",
        "notification",
        "payload",
        "body",
        "target",
        "scheduler execution",
        "gate d",
        "product promise",
    ):
        assert forbidden_fragment not in combined_output


def _assert_session_window_readiness_preflight_output_is_safe(
    stdout: str,
    stderr: str,
) -> None:
    combined_output = f"{stdout}\n{stderr}".lower()
    for forbidden_fragment in (
        "result_kind",
        "title",
        "meeting",
        "meet.example",
        "timezone",
        "duration",
        "confidential",
        "instructor",
        "dr.",
        "lecture",
        "lab",
        "c:\\",
        "\\\\server",
        "/users",
        str(Path.home()).lower(),
        "token",
        "secret",
        "auth",
        "cookie",
        "profile",
        "transcript",
        "audio",
        "browser",
        "session_dir",
        "artifacts",
        "filename",
        "events.jsonl",
        "alerts.log",
        "reviewer.md",
        "runtime.jsonl",
        "benchmark-report.json",
        "sqlite",
        "traceback",
        "live delivery",
        "live-delivery",
        "live_delivery",
        "dispatch",
        "notification",
        "payload",
        "body",
        "target",
        "scheduler execution",
        "gate d",
        "product promise",
    ):
        assert forbidden_fragment not in combined_output


def _assert_session_window_confirmation_preflight_output_is_safe(
    stdout: str,
    stderr: str,
) -> None:
    combined_output = f"{stdout}\n{stderr}".lower()
    for forbidden_fragment in (
        "result_kind",
        "alert_preview",
        "alert_preview_count",
        "archive_",
        "title",
        "meeting",
        "meet.example",
        "timezone",
        "duration",
        "confidential",
        "instructor",
        "dr.",
        "lecture",
        "lab",
        "c:\\",
        "\\\\server",
        "/users",
        str(Path.home()).lower(),
        "token",
        "secret",
        "auth",
        "cookie",
        "profile",
        "transcript",
        "audio",
        "browser",
        "session_dir",
        "artifacts",
        "filename",
        "events.jsonl",
        "alerts.log",
        "reviewer.md",
        "runtime.jsonl",
        "benchmark-report.json",
        "sqlite",
        "traceback",
        "live delivery",
        "live-delivery",
        "live_delivery",
        "dispatch",
        "notification",
        "payload",
        "body",
        "target",
        "scheduler execution",
        "gate d",
        "product promise",
    ):
        assert forbidden_fragment not in combined_output


def _assert_session_window_confirmation_response_output_is_safe(
    stdout: str,
    stderr: str,
) -> None:
    combined_output = f"{stdout}\n{stderr}".lower()
    for forbidden_fragment in (
        "result_kind",
        "alert_preview",
        "alert_preview_count",
        "archive_",
        "title",
        "meeting",
        "meet.example",
        "timezone",
        "duration",
        "confidential",
        "instructor",
        "dr.",
        "lecture",
        "lab",
        "c:\\",
        "\\\\server",
        "/users",
        str(Path.home()).lower(),
        "token",
        "secret",
        "auth",
        "cookie",
        "profile",
        "transcript",
        "audio",
        "browser",
        "session_dir",
        "artifacts",
        "filename",
        "events.jsonl",
        "alerts.log",
        "reviewer.md",
        "runtime.jsonl",
        "benchmark-report.json",
        "sqlite",
        "traceback",
        "live delivery",
        "live-delivery",
        "live_delivery",
        "dispatch",
        "notification",
        "payload",
        "body",
        "target",
        "scheduler execution",
        "gate d",
        "product promise",
    ):
        assert forbidden_fragment not in combined_output


def _assert_scheduled_start_preview_output_is_safe(
    stdout: str,
    stderr: str,
) -> None:
    combined_output = f"{stdout}\n{stderr}".lower()
    for forbidden_fragment in (
        "meeting",
        "timezone",
        "c:\\",
        "\\\\server",
        "/users",
        "token",
        "secret",
        "auth",
        "cookie",
        "profile",
        "transcript",
        "audio",
        "traceback",
        "gate d",
        "product promise",
    ):
        assert forbidden_fragment not in combined_output


def _assert_stored_schedule_preview_output_is_safe(
    stdout: str,
    stderr: str,
) -> None:
    combined_output = f"{stdout}\n{stderr}".lower()
    for forbidden_fragment in (
        "result_kind",
        "enabled",
        "meeting",
        "meet.example",
        "timezone",
        "confidential",
        "instructor",
        "dr.",
        "lecture",
        "lab",
        "c:\\",
        "\\\\server",
        "/users",
        str(Path.home()).lower(),
        "token",
        "secret",
        "auth",
        "cookie",
        "profile",
        "transcript",
        "audio",
        "browser",
        "artifact",
        "select",
        "sqlite",
        "traceback",
        "live",
        "delivery",
        "scheduler execution",
        "gate d",
        "product promise",
    ):
        assert forbidden_fragment not in combined_output


def _assert_stored_schedule_next_preview_output_is_safe(
    stdout: str,
    stderr: str,
) -> None:
    combined_output = f"{stdout}\n{stderr}".lower()
    for forbidden_fragment in (
        "result_kind",
        "enabled",
        "meeting",
        "meet.example",
        "timezone",
        "confidential",
        "instructor",
        "dr.",
        "lecture",
        "lab",
        "c:\\",
        "\\\\server",
        "/users",
        str(Path.home()).lower(),
        "token",
        "secret",
        "auth",
        "cookie",
        "profile",
        "transcript",
        "audio",
        "browser",
        "artifact",
        "sqlite",
        "traceback",
        "live",
        "delivery",
        "scheduler execution",
        "gate d",
        "product promise",
    ):
        assert forbidden_fragment not in combined_output


def _assert_stored_schedule_due_list_output_is_safe(
    stdout: str,
    stderr: str,
) -> None:
    combined_output = f"{stdout}\n{stderr}".lower()
    for forbidden_fragment in (
        "result_kind",
        "enabled",
        "title",
        "meeting",
        "meet.example",
        "timezone",
        "duration",
        "confidential",
        "instructor",
        "dr.",
        "lecture",
        "lab",
        "c:\\",
        "\\\\server",
        "/users",
        str(Path.home()).lower(),
        "token",
        "secret",
        "auth",
        "cookie",
        "profile",
        "transcript",
        "audio",
        "browser",
        "artifact",
        "sqlite",
        "traceback",
        "live",
        "delivery",
        "scheduler execution",
        "gate d",
        "product promise",
    ):
        assert forbidden_fragment not in combined_output


def _assert_course_schedule_save_output_is_safe(
    stdout: str,
    stderr: str,
) -> None:
    combined_output = f"{stdout}\n{stderr}".lower()
    for forbidden_fragment in (
        "title",
        "meeting",
        "meet.example",
        "timezone",
        "duration",
        "confidential",
        "instructor",
        "dr.",
        "lecture",
        "lab",
        "c:\\",
        "\\\\server",
        "/users",
        str(Path.home()).lower(),
        "token",
        "secret",
        "auth",
        "cookie",
        "profile",
        "transcript",
        "audio",
        "browser",
        "artifact",
        "select",
        "sqlite",
        "traceback",
        "live",
        "delivery",
        "scheduler execution",
        "gate d",
        "product promise",
    ):
        assert forbidden_fragment not in combined_output


def _assert_course_schedule_summary_output_is_safe(
    stdout: str,
    stderr: str,
) -> None:
    combined_output = f"{stdout}\n{stderr}".lower()
    for forbidden_fragment in (
        "meeting",
        "meet.example",
        "timezone",
        "confidential",
        "instructor",
        "dr.",
        "lecture",
        "lab",
        "c:\\",
        "\\\\server",
        "/users",
        str(Path.home()).lower(),
        "token",
        "secret",
        "auth",
        "cookie",
        "profile",
        "transcript",
        "audio",
        "browser",
        "artifact",
        "select",
        "sqlite",
        "traceback",
        "gate d",
        "product promise",
    ):
        assert forbidden_fragment not in combined_output


def _assert_course_schedule_list_output_is_safe(
    stdout: str,
    stderr: str,
) -> None:
    combined_output = f"{stdout}\n{stderr}".lower()
    for forbidden_fragment in (
        "title",
        "meeting",
        "meet.example",
        "timezone",
        "duration",
        "confidential",
        "instructor",
        "dr.",
        "lecture",
        "lab",
        "c:\\",
        "\\\\server",
        "/users",
        str(Path.home()).lower(),
        "token",
        "secret",
        "auth",
        "cookie",
        "profile",
        "transcript",
        "audio",
        "browser",
        "artifact",
        "select",
        "sqlite",
        "traceback",
        "live",
        "delivery",
        "scheduler execution",
        "gate d",
        "product promise",
    ):
        assert forbidden_fragment not in combined_output


def test_archive_export_preflight_handler_does_not_execute_export() -> None:
    source = inspect.getsource(cli._run_archive_export_preflight_command)

    assert "execute_archive_export_to_local_root" not in source
    assert "archive_export_execution_result_safe_summary" not in source


def test_archive_export_verify_local_handler_does_not_execute_export() -> None:
    source = inspect.getsource(cli._run_archive_export_verify_local_command)

    assert "execute_archive_export_to_local_root" not in source
    assert "archive_export_execution_result_safe_summary" not in source
    assert "archive_export_verification_summary_safe_summary" in source


def test_archive_delete_dry_run_local_handler_does_not_execute_delete_or_export() -> (
    None
):
    source = inspect.getsource(cli._run_archive_delete_dry_run_local_command)

    assert "build_archive_delete_dry_run_local_result" in source
    assert "export_archive_delete_dry_run_local_result" in source
    for forbidden_fragment in (
        "execute_archive_export_to_local_root",
        "archive_export_execution_result_safe_summary",
        "unlink",
        "remove",
        "rmdir",
        "rmtree",
        "shutil",
        "requests",
        "httpx",
        "playwright",
        "sounddevice",
        "telegram",
        "desktop_notifier",
        "Timer(",
        "threading",
        "asyncio",
    ):
        assert forbidden_fragment not in source


def test_scheduled_start_preview_local_handler_does_not_execute_scheduler() -> None:
    source = inspect.getsource(cli._run_scheduled_start_preview_local_command)

    assert "ScheduleConfig" in source
    assert "build_scheduled_start_plan" in source
    assert "ScheduledStartClock" in source
    assert "build_scheduled_start_manual_result" in source
    assert "scheduled_start_manual_result_safe_summary" in source
    for forbidden_fragment in (
        "datetime",
        "now(",
        "utcnow",
        "sleep",
        "Timer(",
        "threading",
        "subprocess",
        "webbrowser",
        "requests",
        "httpx",
        "playwright",
        "sounddevice",
        "telegram",
        "desktop_notifier",
        "execute_archive",
        "archive_export",
        ".open(",
        ".read_text(",
        ".write_text(",
        ".mkdir(",
        ".unlink(",
        ".remove(",
        ".rmdir(",
    ):
        assert forbidden_fragment not in source


def test_archive_export_cli_source_does_not_call_forbidden_surfaces() -> None:
    source = Path("src/async_scholar/__main__.py").read_text(encoding="utf-8")

    for forbidden_fragment in (
        "archive_delete_confirmation",
        "execute_archive_delete",
        ".unlink(",
        ".remove(",
        ".rmdir(",
        "rmtree",
        "shutil",
        "ZipFile",
        "tarfile",
        "requests",
        "httpx",
        "playwright",
        "sounddevice",
        "faster_whisper",
        "telegram",
        "desktop_notifier",
        "Timer(",
        "threading",
        "asyncio",
        "google",
    ):
        assert forbidden_fragment not in source


def test_mic_recording_diagnostic_command_delegates_to_existing_command(
    monkeypatch,
) -> None:
    received: dict[str, list[str]] = {}
    module_name = "async_scholar.audio.mic_recording_diagnostic"
    fake_module = types.ModuleType(module_name)

    def fake_main(argv: list[str]) -> int:
        received["argv"] = argv
        return 17

    fake_module.main = fake_main
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    exit_code = cli.main(
        [
            "mic-recording-diagnostic",
            "--seconds",
            "1",
            "--max-chunks",
            "1",
        ],
    )

    assert exit_code == 17
    assert received["argv"] == ["--seconds", "1", "--max-chunks", "1"]


def test_fixture_demo_command_writes_artifacts(tmp_path) -> None:
    fixture_path = Path("tests/fixtures/transcripts/attendance_roll_call.jsonl")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "fixture-demo",
            str(fixture_path),
            "--output-root",
            str(tmp_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    output_dir = tmp_path / "fixture_attendance_roll_call"
    assert result.returncode == 0
    assert "Fixture demo complete." in result.stdout
    assert "Events detected: 2" in result.stdout
    assert (output_dir / "events.jsonl").is_file()
    assert (output_dir / "alerts.log").is_file()
    assert (output_dir / "reviewer.md").is_file()
