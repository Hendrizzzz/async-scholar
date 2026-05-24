from __future__ import annotations

import ast
import builtins
import inspect
import json
from pathlib import Path

import pytest

from async_scholar.gate_d_rollback_plan_evidence import (
    GATE_D_ROLLBACK_PLAN_EVIDENCE_ERROR,
    build_local_gate_d_rollback_plan_evidence,
)

EXPECTED_GATE_D_ROLLBACK_PLAN_EVIDENCE = {
    "evidence_kind": "local_gate_d_rollback_plan_evidence",
    "rollback_plan_for_loopback_playwright_spike_status": "satisfactory",
    "rollback_plan_document_status": "tracked",
    "rollback_trigger_coverage_status": "documented",
    "disable_strategy_status": "documented",
    "dependency_rollback_status": "documented",
    "disposable_browser_state_cleanup_status": "documented",
    "artifact_cleanup_status": "documented",
    "private_data_handling_status": "documented",
    "manual_checks_status": "documented",
    "stop_conditions_status": "documented",
    "browser_automation_performed": False,
    "audio_capture_performed": False,
    "loopback_capture_performed": False,
    "network_performed": False,
    "live_delivery_performed": False,
    "filesystem_cleanup_performed": False,
    "dependency_change_performed": False,
    "external_platform_accessed": False,
    "profile_state_accessed": False,
    "gate_d_pass_claimed": False,
    "product_promise_alpha_pass_claimed": False,
}


def test_local_gate_d_rollback_plan_evidence_returns_exact_allowlisted_output() -> None:
    payload = build_local_gate_d_rollback_plan_evidence()

    assert type(payload) is dict
    assert payload == EXPECTED_GATE_D_ROLLBACK_PLAN_EVIDENCE
    assert list(payload) == list(EXPECTED_GATE_D_ROLLBACK_PLAN_EVIDENCE)
    assert json.loads(json.dumps(payload)) == payload
    _assert_rollback_plan_evidence_output_is_safe(payload)


def test_local_gate_d_rollback_plan_evidence_accepts_no_input() -> None:
    assert inspect.signature(build_local_gate_d_rollback_plan_evidence).parameters == {}


def test_tracked_rollback_plan_document_contains_required_safety_sections() -> None:
    text = Path("docs/gate-d-loopback-playwright-rollback-plan.md").read_text(
        encoding="utf-8"
    )
    normalized_text = " ".join(text.split())

    for heading in (
        "## Status",
        "## Scope",
        "## Rollback Triggers",
        "## Disable Strategy",
        "## Dependency Rollback",
        "## Browser Binary And Profile Cleanup",
        "## Artifact Inventory And Cleanup",
        "## Secret, Auth, And Private-Data Handling",
        "## Confirmation And Policy Gates",
        "## Verification Commands",
        "## Manual Checks",
        "## Stop Conditions",
    ):
        assert heading in text

    for boundary in (
        "does not approve Gate D",
        "Product Promise Alpha",
        "browser automation",
        "loopback or",
        "system audio capture",
        "real meeting access",
        "live delivery",
        "separate ticket",
        "explicit user approval",
        "Do not use a real user browser profile",
        "Do not persist browser auth state",
        "Do not commit browser artifacts",
        "true human-only gates",
    ):
        assert boundary in normalized_text


def test_local_gate_d_rollback_plan_evidence_source_guards_forbidden_surfaces() -> None:
    source = Path("src/async_scholar/gate_d_rollback_plan_evidence.py").read_text(
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
        "subprocess",
        "powershell",
        "socket",
        "urlopen(",
        "requests",
        "httpx",
        "selenium",
        "webbrowser",
        "browser.new",
        "chromium",
        "firefox",
        "cookie",
        "auth_state",
        "profile_dir",
        "meeting_url",
        "google",
        "meet.",
        "sounddevice",
        "faster_whisper",
        "microphone",
        "system audio",
        "scheduler",
        "session_window",
        "archive_delete",
        "archive_export",
        "dispatch",
        "telegram",
        "desktop",
        "sleep",
        "timer(",
        "threading",
        "asyncio",
        "__import__",
        "eval(",
        "exec(",
    ):
        assert forbidden_fragment not in source_lower


def test_local_gate_d_rollback_plan_evidence_sanitizes_malformed_internal_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_payload() -> dict[str, object]:
        return {"private": "C:/Users/student/token-secret-auth-profile"}

    monkeypatch.setattr(
        "async_scholar.gate_d_rollback_plan_evidence._build_payload",
        fake_payload,
    )

    with pytest.raises(ValueError) as exc_info:
        build_local_gate_d_rollback_plan_evidence()

    assert str(exc_info.value) == GATE_D_ROLLBACK_PLAN_EVIDENCE_ERROR
    assert exc_info.value.__cause__ is None
    _assert_error_is_sanitized(str(exc_info.value))


def test_local_gate_d_rollback_plan_evidence_sanitizes_internal_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_payload() -> dict[str, object]:
        raise RuntimeError("C:\\Users\\student\\.env BOT_TOKEN=secret traceback")

    monkeypatch.setattr(
        "async_scholar.gate_d_rollback_plan_evidence._build_payload",
        fake_payload,
    )

    with pytest.raises(ValueError) as exc_info:
        build_local_gate_d_rollback_plan_evidence()

    assert str(exc_info.value) == GATE_D_ROLLBACK_PLAN_EVIDENCE_ERROR
    assert exc_info.value.__cause__ is None
    _assert_error_is_sanitized(str(exc_info.value))


def test_local_gate_d_rollback_plan_evidence_output_privacy_guards() -> None:
    payload = build_local_gate_d_rollback_plan_evidence()

    assert payload["browser_automation_performed"] is False
    assert payload["audio_capture_performed"] is False
    assert payload["loopback_capture_performed"] is False
    assert payload["network_performed"] is False
    assert payload["live_delivery_performed"] is False
    assert payload["filesystem_cleanup_performed"] is False
    assert payload["dependency_change_performed"] is False
    assert payload["external_platform_accessed"] is False
    assert payload["profile_state_accessed"] is False
    assert payload["gate_d_pass_claimed"] is False
    assert payload["product_promise_alpha_pass_claimed"] is False
    _assert_rollback_plan_evidence_output_is_safe(payload)


def test_local_gate_d_rollback_plan_evidence_does_not_touch_runtime_file_io(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_open(*args: object, **kwargs: object) -> object:
        raise AssertionError("production helper must not open files")

    monkeypatch.setattr(builtins, "open", fail_open)

    assert (
        build_local_gate_d_rollback_plan_evidence()
        == EXPECTED_GATE_D_ROLLBACK_PLAN_EVIDENCE
    )


def _assert_rollback_plan_evidence_output_is_safe(payload: dict[str, object]) -> None:
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
        "secret",
        "chat",
        "cookie",
        "auth-profile",
        "raw",
        "exception",
        "traceback",
        "powershell",
        "selenium",
        "loopback capture approved",
        "browser automation approved",
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
