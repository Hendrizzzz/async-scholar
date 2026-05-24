from __future__ import annotations

import ast
import inspect
import json

import pytest

from async_scholar import policy_gate_smoke
from async_scholar.policy_gate_smoke import (
    POLICY_GATE_SMOKE_ERROR,
    build_local_policy_gate_smoke,
)

EXPECTED_POLICY_GATE_SMOKE_RESULT = {
    "academic_answer_generated": False,
    "alert_requires_confirmation": True,
    "declined_confirmation_blocks_authorization": True,
    "gate_d_pass_claimed": False,
    "live_delivery_performed": False,
    "malformed_authorization_rejected": True,
    "malformed_confirmation_rejected": True,
    "participation_action_performed": False,
    "policy_gate_tests_status": "satisfactory",
    "product_promise_alpha_pass_claimed": False,
    "smoke_kind": "local_policy_gate",
    "start_authorization_status": "blocked",
    "start_block_reason": "confirmation_declined",
}


def test_local_policy_gate_smoke_builds_allowlisted_satisfactory_summary() -> None:
    result = build_local_policy_gate_smoke()

    assert result == EXPECTED_POLICY_GATE_SMOKE_RESULT
    assert set(result) == set(EXPECTED_POLICY_GATE_SMOKE_RESULT)
    assert json.loads(json.dumps(result)) == result
    _assert_policy_gate_smoke_output_is_safe(result)


def test_local_policy_gate_smoke_accepts_no_private_or_free_form_input() -> None:
    assert inspect.signature(build_local_policy_gate_smoke).parameters == {}


def test_local_policy_gate_smoke_fails_closed_if_alert_confirmation_is_missing(
    monkeypatch,
) -> None:
    def fake_payload(event_type: str) -> dict[str, object]:
        return {
            "severity": "urgent",
            "title": "private title should not leak",
            "body": "private body should not leak",
            "requires_confirmation": False,
        }

    monkeypatch.setattr(
        policy_gate_smoke, "build_alert_notification_payload", fake_payload
    )

    with pytest.raises(ValueError, match=POLICY_GATE_SMOKE_ERROR) as exc_info:
        build_local_policy_gate_smoke()

    assert str(exc_info.value) == POLICY_GATE_SMOKE_ERROR
    assert exc_info.value.__cause__ is None


def test_local_policy_gate_smoke_sanitizes_underlying_failures(monkeypatch) -> None:
    def fake_authorization(payload: dict[str, object]) -> dict[str, object]:
        raise RuntimeError("C:\\Users\\student\\.env BOT_TOKEN=secret traceback")

    monkeypatch.setattr(
        policy_gate_smoke,
        "build_session_window_start_authorization_summary",
        fake_authorization,
    )

    with pytest.raises(ValueError, match=POLICY_GATE_SMOKE_ERROR) as exc_info:
        build_local_policy_gate_smoke()

    assert str(exc_info.value) == POLICY_GATE_SMOKE_ERROR
    assert exc_info.value.__cause__ is None
    assert "BOT_TOKEN" not in str(exc_info.value)
    assert "secret" not in str(exc_info.value)
    assert "Users" not in str(exc_info.value)


def test_local_policy_gate_smoke_source_has_no_forbidden_surfaces() -> None:
    source = inspect.getsource(policy_gate_smoke)
    source_lower = source.lower()
    parsed = ast.parse(source)

    imported_names: set[str] = set()
    for node in ast.walk(parsed):
        if isinstance(node, ast.Import):
            imported_names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_names.add(node.module)

    for forbidden_import in (
        "pathlib",
        "sqlite3",
        "async_scholar.schedule_store",
        "async_scholar.alert_dispatch",
        "async_scholar.alert_routing_smoke",
        "async_scholar.telegram_notifier",
        "async_scholar.desktop_notifier",
        "subprocess",
        "socket",
        "urllib",
        "requests",
        "httpx",
        "playwright",
        "selenium",
        "webbrowser",
        "sounddevice",
        "asyncio",
        "threading",
        "time",
    ):
        assert forbidden_import not in imported_names

    for forbidden_fragment in (
        "dispatch_alert",
        "telegram",
        "desktop_notifier",
        "subprocess",
        "powershell",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "playwright",
        "selenium",
        "webbrowser",
        "sounddevice",
        "faster_whisper",
        "loopback",
        "browser",
        "cookie",
        "profile",
        "meeting",
        "transcript",
        "question",
        "token",
        "secret",
        "path(",
        ".open(",
        "read_text",
        "write_text",
        "mkdir",
        "unlink",
        "remove",
        "rmdir",
        "rmtree",
        "sleep",
        "timer(",
        "threading",
        "asyncio",
        "__import__",
        "eval(",
        "exec(",
    ):
        assert forbidden_fragment not in source_lower


def _assert_policy_gate_smoke_output_is_safe(result: dict[str, object]) -> None:
    assert result["participation_action_performed"] is False
    assert result["academic_answer_generated"] is False
    assert result["live_delivery_performed"] is False
    assert result["gate_d_pass_claimed"] is False
    assert result["product_promise_alpha_pass_claimed"] is False

    serialized = json.dumps(result).lower()
    for forbidden_fragment in (
        "title",
        "body",
        "message",
        "event_id",
        "session_id",
        "source_segment",
        "course_id",
        "courses",
        "meeting",
        "meet.example",
        "google",
        "http://",
        "https://",
        "c:\\",
        "\\\\server",
        "/users",
        ".env",
        "token",
        "secret",
        "cookie",
        "browser",
        "profile",
        "transcript",
        "audio",
        "camera",
        "raw",
        "exception",
        "traceback",
        "telegram",
        "desktop",
        "notify",
        "subprocess",
        "powershell",
        "playwright",
        "loopback",
        "scheduler execution",
        "gate d passed",
        "product promise alpha passed",
    ):
        assert forbidden_fragment not in serialized
