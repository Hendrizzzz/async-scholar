from __future__ import annotations

import ast
import builtins
import inspect
import json
from pathlib import Path

import pytest

from async_scholar.gate_d_security_review_evidence import (
    GATE_D_SECURITY_REVIEW_EVIDENCE_ERROR,
    build_local_gate_d_security_review_evidence,
)

EXPECTED_GATE_D_SECURITY_REVIEW_EVIDENCE = {
    "evidence_kind": "local_gate_d_security_review_evidence",
    "security_review_status": "satisfactory",
    "privacy_boundary_review_status": "satisfactory",
    "sanitized_output_review_status": "satisfactory",
    "secret_handling_review_status": "satisfactory",
    "private_data_boundary_review_status": "satisfactory",
    "browser_auth_boundary_review_status": "satisfactory",
    "audio_capture_boundary_review_status": "satisfactory",
    "scheduler_execution_boundary_review_status": "satisfactory",
    "deletion_export_boundary_review_status": "satisfactory",
    "browser_automation_performed": False,
    "auth_profile_accessed": False,
    "cookie_accessed": False,
    "private_data_read": False,
    "audio_capture_performed": False,
    "loopback_capture_performed": False,
    "network_performed": False,
    "scheduler_execution_performed": False,
    "live_delivery_performed": False,
    "cleanup_or_deletion_performed": False,
    "export_performed": False,
    "subprocess_performed": False,
    "timer_or_sleep_used": False,
    "dependency_change_performed": False,
    "public_github_approval_claimed": False,
    "gate_d_pass_claimed": False,
    "product_promise_alpha_pass_claimed": False,
    "autonomous_participation_performed": False,
    "academic_answer_behavior_performed": False,
}


def test_local_gate_d_security_review_evidence_returns_exact_allowlisted_output() -> (
    None
):
    payload = build_local_gate_d_security_review_evidence()

    assert type(payload) is dict
    assert payload == EXPECTED_GATE_D_SECURITY_REVIEW_EVIDENCE
    assert list(payload) == list(EXPECTED_GATE_D_SECURITY_REVIEW_EVIDENCE)
    assert json.loads(json.dumps(payload)) == payload
    _assert_security_review_evidence_output_is_safe(payload)


def test_local_gate_d_security_review_evidence_accepts_no_input() -> None:
    signature = inspect.signature(build_local_gate_d_security_review_evidence)

    assert signature.parameters == {}


def test_local_gate_d_security_review_evidence_source_guards_forbidden_surfaces() -> (
    None
):
    source = Path("src/async_scholar/gate_d_security_review_evidence.py").read_text(
        encoding="utf-8"
    )
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
        "browser.new",
        "chromium",
        "firefox",
        "auth_state",
        "profile_dir",
        "browser_profile",
        "meeting_url",
        "google",
        "meet.",
        "sounddevice",
        "faster_whisper",
        "microphone",
        "system audio",
        "scheduler.",
        "scheduler_execute",
        "scheduler_loop",
        "session_window",
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


def test_local_gate_d_security_review_evidence_sanitizes_malformed_internal_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_payload() -> dict[str, object]:
        return {"private": "C:/Users/student/token-secret-auth-profile"}

    monkeypatch.setattr(
        "async_scholar.gate_d_security_review_evidence._build_payload",
        fake_payload,
    )

    with pytest.raises(ValueError) as exc_info:
        build_local_gate_d_security_review_evidence()

    assert str(exc_info.value) == GATE_D_SECURITY_REVIEW_EVIDENCE_ERROR
    assert exc_info.value.__cause__ is None
    _assert_error_is_sanitized(str(exc_info.value))


def test_local_gate_d_security_review_evidence_sanitizes_internal_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_payload() -> dict[str, object]:
        raise RuntimeError("C:\\Users\\student\\.env BOT_TOKEN=secret traceback")

    monkeypatch.setattr(
        "async_scholar.gate_d_security_review_evidence._build_payload",
        fake_payload,
    )

    with pytest.raises(ValueError) as exc_info:
        build_local_gate_d_security_review_evidence()

    assert str(exc_info.value) == GATE_D_SECURITY_REVIEW_EVIDENCE_ERROR
    assert exc_info.value.__cause__ is None
    _assert_error_is_sanitized(str(exc_info.value))


def test_local_gate_d_security_review_evidence_output_privacy_guards() -> None:
    payload = build_local_gate_d_security_review_evidence()

    assert payload["browser_automation_performed"] is False
    assert payload["auth_profile_accessed"] is False
    assert payload["cookie_accessed"] is False
    assert payload["private_data_read"] is False
    assert payload["audio_capture_performed"] is False
    assert payload["loopback_capture_performed"] is False
    assert payload["network_performed"] is False
    assert payload["scheduler_execution_performed"] is False
    assert payload["live_delivery_performed"] is False
    assert payload["cleanup_or_deletion_performed"] is False
    assert payload["export_performed"] is False
    assert payload["subprocess_performed"] is False
    assert payload["timer_or_sleep_used"] is False
    assert payload["dependency_change_performed"] is False
    assert payload["public_github_approval_claimed"] is False
    assert payload["gate_d_pass_claimed"] is False
    assert payload["product_promise_alpha_pass_claimed"] is False
    assert payload["autonomous_participation_performed"] is False
    assert payload["academic_answer_behavior_performed"] is False
    _assert_security_review_evidence_output_is_safe(payload)


def test_local_gate_d_security_review_evidence_does_not_touch_runtime_file_io(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_open(*args: object, **kwargs: object) -> object:
        raise AssertionError("production helper must not open files")

    monkeypatch.setattr(builtins, "open", fail_open)

    assert (
        build_local_gate_d_security_review_evidence()
        == EXPECTED_GATE_D_SECURITY_REVIEW_EVIDENCE
    )


def _assert_security_review_evidence_output_is_safe(payload: dict[str, object]) -> None:
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
        "gate d passed",
        "product promise alpha passed",
        "online monitoring approved",
        "execution approved",
        "public github approved",
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
