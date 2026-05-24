from __future__ import annotations

import ast
import builtins
import inspect
import json
from pathlib import Path

import pytest

from async_scholar.gate_d_mic_diagnostics_after_reboot_evidence import (
    GATE_D_MIC_DIAGNOSTICS_AFTER_REBOOT_EVIDENCE_ERROR,
    build_local_gate_d_mic_diagnostics_after_reboot_evidence,
)

EXPECTED_GATE_D_MIC_DIAGNOSTICS_AFTER_REBOOT_EVIDENCE = {
    "evidence_kind": "local_gate_d_mic_diagnostics_after_reboot_evidence",
    "mic_diagnostics_after_reboot_status": "satisfactory",
    "recorded_scalar_post_reboot_evidence_status": "satisfactory",
    "metadata_only_evidence_status": "documented",
    "no_signal_quality_claim_status": "documented",
    "no_transcript_usefulness_claim_status": "documented",
    "local_only_status": "documented",
    "file_io_performed": False,
    "artifact_read": False,
    "artifact_created": False,
    "device_name_exposed": False,
    "private_path_exposed": False,
    "transcript_text_exposed": False,
    "audio_capture_performed": False,
    "recording_performed": False,
    "vad_performed": False,
    "stt_performed": False,
    "signal_quality_claimed": False,
    "transcript_usefulness_claimed": False,
    "network_performed": False,
    "browser_automation_performed": False,
    "auth_profile_accessed": False,
    "cookie_accessed": False,
    "private_data_read": False,
    "scheduler_execution_performed": False,
    "live_delivery_performed": False,
    "cleanup_or_deletion_performed": False,
    "export_performed": False,
    "dependency_change_performed": False,
    "gate_d_pass_claimed": False,
    "product_promise_alpha_pass_claimed": False,
    "autonomous_participation_performed": False,
    "academic_answer_behavior_performed": False,
}


def test_local_gate_d_mic_after_reboot_evidence_returns_exact_allowlist() -> None:
    payload = build_local_gate_d_mic_diagnostics_after_reboot_evidence()

    assert type(payload) is dict
    assert payload == EXPECTED_GATE_D_MIC_DIAGNOSTICS_AFTER_REBOOT_EVIDENCE
    assert list(payload) == list(EXPECTED_GATE_D_MIC_DIAGNOSTICS_AFTER_REBOOT_EVIDENCE)
    assert json.loads(json.dumps(payload)) == payload
    _assert_mic_diagnostics_after_reboot_evidence_output_is_safe(payload)


def test_local_gate_d_mic_diagnostics_after_reboot_evidence_accepts_no_input() -> None:
    signature = inspect.signature(
        build_local_gate_d_mic_diagnostics_after_reboot_evidence
    )

    assert signature.parameters == {}


def test_local_gate_d_mic_diagnostics_after_reboot_evidence_source_guards() -> None:
    source = Path(
        "src/async_scholar/gate_d_mic_diagnostics_after_reboot_evidence.py"
    ).read_text(encoding="utf-8")
    source_lower = source.lower()
    parsed = ast.parse(source)

    imported_names: set[str] = set()
    for node in ast.walk(parsed):
        if isinstance(node, ast.Import):
            imported_names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_names.add(node.module)

    assert imported_names == {"__future__", "typing"}

    for forbidden_fragment in (
        "pathlib",
        "sqlite3",
        "open(",
        "read_text",
        "write_text",
        "mkdir",
        "unlink",
        "remove(",
        "rmdir",
        "rmtree",
        "subprocess.",
        "popen",
        "powershell",
        "socket",
        "urlopen(",
        "requests",
        "httpx",
        "playwright",
        "selenium",
        "webbrowser",
        "sounddevice",
        "faster_whisper",
        "whisper",
        "microphone",
        "system audio",
        "loopback",
        "vad.",
        "stt.",
        "record(",
        "recording.",
        "audio.",
        "wave",
        "wav",
        "signal_quality(",
        "schedule_store",
        "scheduled_start",
        "session_window",
        "scheduler.",
        "archive_delete",
        "archive_export",
        "dispatch",
        "telegram",
        "desktop",
        ".sleep(",
        "sleep(",
        "timer(",
        "threading",
        "asyncio",
        "__import__",
        "eval(",
        "exec(",
    ):
        assert forbidden_fragment not in source_lower


def test_local_gate_d_mic_diagnostics_after_reboot_evidence_sanitizes_malformed_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_payload() -> dict[str, object]:
        return {"private": "C:/Users/student/token-secret-auth-profile"}

    monkeypatch.setattr(
        "async_scholar.gate_d_mic_diagnostics_after_reboot_evidence._build_payload",
        fake_payload,
    )

    with pytest.raises(ValueError) as exc_info:
        build_local_gate_d_mic_diagnostics_after_reboot_evidence()

    assert str(exc_info.value) == GATE_D_MIC_DIAGNOSTICS_AFTER_REBOOT_EVIDENCE_ERROR
    assert exc_info.value.__cause__ is None
    _assert_error_is_sanitized(str(exc_info.value))


def test_local_gate_d_mic_diagnostics_after_reboot_evidence_sanitizes_internal_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_payload() -> dict[str, object]:
        raise RuntimeError("C:\\Users\\student\\.env BOT_TOKEN=secret traceback")

    monkeypatch.setattr(
        "async_scholar.gate_d_mic_diagnostics_after_reboot_evidence._build_payload",
        fake_payload,
    )

    with pytest.raises(ValueError) as exc_info:
        build_local_gate_d_mic_diagnostics_after_reboot_evidence()

    assert str(exc_info.value) == GATE_D_MIC_DIAGNOSTICS_AFTER_REBOOT_EVIDENCE_ERROR
    assert exc_info.value.__cause__ is None
    _assert_error_is_sanitized(str(exc_info.value))


def test_local_gate_d_mic_diagnostics_after_reboot_evidence_output_privacy_guards() -> (
    None
):
    payload = build_local_gate_d_mic_diagnostics_after_reboot_evidence()

    assert payload["file_io_performed"] is False
    assert payload["artifact_read"] is False
    assert payload["artifact_created"] is False
    assert payload["device_name_exposed"] is False
    assert payload["private_path_exposed"] is False
    assert payload["transcript_text_exposed"] is False
    assert payload["audio_capture_performed"] is False
    assert payload["recording_performed"] is False
    assert payload["vad_performed"] is False
    assert payload["stt_performed"] is False
    assert payload["signal_quality_claimed"] is False
    assert payload["transcript_usefulness_claimed"] is False
    assert payload["network_performed"] is False
    assert payload["browser_automation_performed"] is False
    assert payload["auth_profile_accessed"] is False
    assert payload["cookie_accessed"] is False
    assert payload["private_data_read"] is False
    assert payload["scheduler_execution_performed"] is False
    assert payload["live_delivery_performed"] is False
    assert payload["cleanup_or_deletion_performed"] is False
    assert payload["export_performed"] is False
    assert payload["dependency_change_performed"] is False
    assert payload["gate_d_pass_claimed"] is False
    assert payload["product_promise_alpha_pass_claimed"] is False
    assert payload["autonomous_participation_performed"] is False
    assert payload["academic_answer_behavior_performed"] is False
    _assert_mic_diagnostics_after_reboot_evidence_output_is_safe(payload)


def test_local_gate_d_mic_diagnostics_after_reboot_evidence_does_not_touch_file_io(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_open(*args: object, **kwargs: object) -> object:
        raise AssertionError("production helper must not open files")

    monkeypatch.setattr(builtins, "open", fail_open)

    assert (
        build_local_gate_d_mic_diagnostics_after_reboot_evidence()
        == EXPECTED_GATE_D_MIC_DIAGNOSTICS_AFTER_REBOOT_EVIDENCE
    )


def _assert_mic_diagnostics_after_reboot_evidence_output_is_safe(
    payload: dict[str, object],
) -> None:
    combined_output = json.dumps(payload, sort_keys=True).lower()
    for forbidden_fragment in (
        "title",
        "body",
        "provider",
        "http_status",
        "message",
        "request",
        "url",
        "command",
        "event_id",
        "session_id",
        "source_segment",
        "course_id",
        "meeting",
        "meet.example",
        "meet.google",
        "http://",
        "https://",
        "c:\\",
        "\\\\server",
        "/users",
        ".env",
        "token",
        "chat",
        "raw",
        "exception",
        "traceback",
        "powershell",
        "playwright",
        "selenium",
        "sounddevice",
        "faster_whisper",
        "microphone",
        "device name",
        "gate d passed",
        "product promise alpha passed",
        "online monitoring approved",
        "execution approved",
    ):
        assert forbidden_fragment not in combined_output


def _assert_error_is_sanitized(error_text: str) -> None:
    for forbidden_fragment in (
        "C:\\Users",
        "C:/Users",
        "student",
        ".env",
        "BOT_TOKEN",
        "secret",
        "token",
        "auth",
        "profile",
        "private",
        "traceback",
    ):
        assert forbidden_fragment not in error_text
