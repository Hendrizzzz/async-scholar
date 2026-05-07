from __future__ import annotations

import json
from dataclasses import dataclass
from typing import cast

import pytest

from async_scholar.alert_dispatch import (
    AlertDispatchErrorKind,
    AlertDispatchResult,
    build_urgent_alert_retry_log_decisions,
    dispatch_alert,
)
from async_scholar.alerts import build_alert_notification_payload
from async_scholar.schemas import LectureEvent


def _event(
    event_type: str = "attendance_prompt",
    *,
    message: str = "Instructor asked for attendance.",
) -> LectureEvent:
    return LectureEvent(
        event_id="event-1",
        session_id="session-1",
        event_type=event_type,
        detected_at_seconds=12.5,
        source_segment_ids=["segment-1"],
        message=message,
    )


def _dispatch_result(
    provider: str,
    *,
    severity: str = "urgent",
    status: str = "failed",
    error_kind: AlertDispatchErrorKind | None = None,
) -> AlertDispatchResult:
    result = {
        "provider": provider,
        "severity": severity,
        "status": status,
        "requires_confirmation": True,
    }
    if error_kind is not None:
        result["error_kind"] = error_kind
    return cast(AlertDispatchResult, result)


def test_dispatch_alert_uses_injected_dispatcher_and_sanitizes_success() -> None:
    calls: list[object] = []

    def dispatcher(payload: object) -> dict[str, str]:
        calls.append(payload)
        return {"status": "sent", "raw_response": "provider internals stay out"}

    results = dispatch_alert(
        _event(),
        provider_names=["console"],
        dispatchers={"console": dispatcher},
    )

    assert calls == [build_alert_notification_payload("attendance_prompt")]
    assert results == [
        {
            "provider": "console",
            "severity": "urgent",
            "status": "sent",
            "requires_confirmation": True,
        }
    ]


def test_dispatch_alert_reports_missing_dispatcher_as_sanitized_skip() -> None:
    results = dispatch_alert(
        _event("direct_question"),
        provider_names=["desktop"],
        dispatchers={},
    )

    assert results == [
        {
            "provider": "desktop",
            "severity": "normal",
            "status": "skipped",
            "requires_confirmation": True,
            "error_kind": "missing_dispatcher",
        }
    ]


def test_dispatch_alert_normalizes_dispatcher_failure_without_exception_text() -> None:
    def dispatcher(payload: object) -> None:
        raise RuntimeError(
            "BOT_TOKEN=secret-token C:\\Users\\student\\.env chat_id=12345"
        )

    results = dispatch_alert(
        _event("quiz_prompt"),
        provider_names=["telegram"],
        dispatchers={"telegram": dispatcher},
    )

    assert results == [
        {
            "provider": "telegram",
            "severity": "urgent",
            "status": "failed",
            "requires_confirmation": True,
            "error_kind": "provider_error",
        }
    ]
    serialized = json.dumps(results)
    assert "secret-token" not in serialized
    assert ".env" not in serialized
    assert "12345" not in serialized


def test_dispatch_alert_normalizes_unsupported_provider_result() -> None:
    def dispatcher(payload: object) -> dict[str, str]:
        return {
            "status": "unsupported",
            "error": "unsupported because token=secret",
        }

    results = dispatch_alert(
        _event("dismissal_cue"),
        provider_names=["desktop"],
        dispatchers={"desktop": dispatcher},
    )

    assert results == [
        {
            "provider": "desktop",
            "severity": "low",
            "status": "skipped",
            "requires_confirmation": True,
            "error_kind": "unsupported_provider",
        }
    ]


def test_dispatch_alert_normalizes_object_unsupported_result_as_skip() -> None:
    @dataclass(frozen=True)
    class ProviderResult:
        status: str
        error_kind: str
        raw_details: str

    def dispatcher(payload: object) -> ProviderResult:
        return ProviderResult(
            status="unsupported",
            error_kind="unsupported_platform",
            raw_details="unsupported on C:\\Users\\student\\.env",
        )

    results = dispatch_alert(
        _event("dismissal_cue"),
        provider_names=["desktop"],
        dispatchers={"desktop": dispatcher},
    )

    assert results == [
        {
            "provider": "desktop",
            "severity": "low",
            "status": "skipped",
            "requires_confirmation": True,
            "error_kind": "unsupported_platform",
        }
    ]
    serialized = json.dumps(results)
    assert ".env" not in serialized
    assert "student" not in serialized


@pytest.mark.parametrize(
    "error_kind",
    [
        "missing_dispatcher",
        "provider_error",
        "unsupported_provider",
        "unsupported_platform",
        "command_failed",
        "command_failure",
        "timeout",
        "os_error",
        "network_error",
        "http_error",
        "missing_credentials",
    ],
)
def test_dispatch_alert_normalizes_object_failed_result_with_allowlisted_error_kind(
    error_kind: str,
) -> None:
    @dataclass(frozen=True)
    class ProviderResult:
        status: str
        error_kind: str
        stderr: str
        request_url: str

    def dispatcher(payload: object) -> ProviderResult:
        return ProviderResult(
            status="failed",
            error_kind=error_kind,
            stderr="BOT_TOKEN=secret-token stderr should not leak",
            request_url="https://api.telegram.example/bot-secret/sendMessage",
        )

    results = dispatch_alert(
        _event("quiz_prompt"),
        provider_names=["telegram"],
        dispatchers={"telegram": dispatcher},
    )

    assert results == [
        {
            "provider": "telegram",
            "severity": "urgent",
            "status": "failed",
            "requires_confirmation": True,
            "error_kind": error_kind,
        }
    ]
    serialized = json.dumps(results)
    assert "secret-token" not in serialized
    assert "sendMessage" not in serialized


def test_dispatch_alert_keeps_telegram_mapping_failed_result_sanitized() -> None:
    def dispatcher(payload: object) -> dict[str, str]:
        return {
            "status": "failed",
            "error_kind": "http_error",
            "url": "https://api.telegram.example/bot-secret/sendMessage",
            "body": "chat_id=12345",
        }

    results = dispatch_alert(
        _event("attendance_prompt"),
        provider_names=["telegram"],
        dispatchers={"telegram": dispatcher},
    )

    assert results == [
        {
            "provider": "telegram",
            "severity": "urgent",
            "status": "failed",
            "requires_confirmation": True,
            "error_kind": "http_error",
        }
    ]
    serialized = json.dumps(results)
    assert "bot-secret" not in serialized
    assert "12345" not in serialized


def test_dispatch_alert_normalizes_unknown_status_as_sanitized_failure() -> None:
    def dispatcher(payload: object) -> dict[str, str]:
        return {
            "status": "sent BOT_TOKEN=secret-token",
            "error_kind": "provider_error",
            "stdout": "raw transcript answer",
        }

    results = dispatch_alert(
        _event("direct_question"),
        provider_names=["desktop"],
        dispatchers={"desktop": dispatcher},
    )

    assert results == [
        {
            "provider": "desktop",
            "severity": "normal",
            "status": "failed",
            "requires_confirmation": True,
            "error_kind": "provider_error",
        }
    ]
    serialized = json.dumps(results)
    assert "secret-token" not in serialized
    assert "raw transcript" not in serialized


def test_dispatch_alert_normalizes_unknown_error_kind_as_sanitized_failure() -> None:
    @dataclass(frozen=True)
    class ProviderResult:
        status: str
        error_kind: str
        exception_text: str

    def dispatcher(payload: object) -> ProviderResult:
        return ProviderResult(
            status="skipped",
            error_kind="C:\\Users\\student\\.env BOT_TOKEN=secret-token",
            exception_text="raw OS exception with private path",
        )

    results = dispatch_alert(
        _event("camera_mic_request"),
        provider_names=["desktop"],
        dispatchers={"desktop": dispatcher},
    )

    assert results == [
        {
            "provider": "desktop",
            "severity": "urgent",
            "status": "failed",
            "requires_confirmation": True,
            "error_kind": "provider_error",
        }
    ]
    serialized = json.dumps(results)
    assert ".env" not in serialized
    assert "secret-token" not in serialized
    assert "raw OS exception" not in serialized


def test_dispatch_alert_preserves_multiple_provider_order() -> None:
    def dispatcher(payload: object) -> None:
        return None

    results = dispatch_alert(
        _event(),
        provider_names=["telegram", "desktop", "console"],
        dispatchers={
            "console": dispatcher,
            "desktop": dispatcher,
            "telegram": dispatcher,
        },
    )

    assert [result["provider"] for result in results] == [
        "telegram",
        "desktop",
        "console",
    ]
    assert [result["status"] for result in results] == ["sent", "sent", "sent"]


def test_dispatch_alert_does_not_leak_suspicious_event_content() -> None:
    leaked_strings = [
        "BOT_TOKEN=secret-token",
        "C:\\Users\\student\\lecture.wav",
        "chat_id=12345",
        "segment-secret",
        "event-secret",
        "session-secret",
        "raw transcript answer",
    ]
    captured_payloads: list[object] = []

    def dispatcher(payload: object) -> dict[str, str]:
        captured_payloads.append(payload)
        return {
            "status": "sent",
            "message": "BOT_TOKEN=provider-secret should not leak",
        }

    event = LectureEvent(
        event_id="event-secret",
        session_id="session-secret",
        event_type="BOT_TOKEN=secret-token C:\\Users\\student\\lecture.wav",
        detected_at_seconds=99.0,
        source_segment_ids=["segment-secret"],
        message="raw transcript answer with chat_id=12345",
    )

    results = dispatch_alert(
        event,
        provider_names=["telegram"],
        dispatchers={"telegram": dispatcher},
    )

    assert results == [
        {
            "provider": "telegram",
            "severity": "normal",
            "status": "sent",
            "requires_confirmation": True,
        }
    ]
    serialized_results = json.dumps(results)
    serialized_payload = json.dumps(captured_payloads)
    for leaked_string in leaked_strings:
        assert leaked_string not in serialized_results
        assert leaked_string not in serialized_payload


@pytest.mark.parametrize(
    "error_kind",
    [
        "provider_error",
        "timeout",
        "network_error",
        "http_error",
        "command_failed",
        "command_failure",
        "os_error",
    ],
)
def test_retry_log_decisions_classify_urgent_retryable_failures(
    error_kind: AlertDispatchErrorKind,
) -> None:
    decisions = build_urgent_alert_retry_log_decisions(
        [_dispatch_result("telegram", error_kind=error_kind)]
    )

    assert decisions == [
        {
            "provider": "telegram",
            "severity": "urgent",
            "status": "failed",
            "requires_confirmation": True,
            "error_kind": error_kind,
            "retry_action": "retry",
            "max_attempts": 3,
        }
    ]
    assert set(decisions[0]) == {
        "provider",
        "severity",
        "status",
        "requires_confirmation",
        "error_kind",
        "retry_action",
        "max_attempts",
    }


@pytest.mark.parametrize(
    ("status", "error_kind"),
    [
        ("skipped", "missing_dispatcher"),
        ("skipped", "unsupported_provider"),
        ("failed", "unsupported_platform"),
        ("failed", "missing_credentials"),
    ],
)
def test_retry_log_decisions_classify_urgent_non_retryable_issues(
    status: str,
    error_kind: AlertDispatchErrorKind,
) -> None:
    decisions = build_urgent_alert_retry_log_decisions(
        [_dispatch_result("desktop", status=status, error_kind=error_kind)]
    )

    assert decisions == [
        {
            "provider": "desktop",
            "severity": "urgent",
            "status": status,
            "requires_confirmation": True,
            "error_kind": error_kind,
            "retry_action": "manual_check",
            "max_attempts": 0,
        }
    ]


def test_retry_log_decisions_omit_urgent_sent_results() -> None:
    decisions = build_urgent_alert_retry_log_decisions(
        [_dispatch_result("telegram", status="sent")]
    )

    assert decisions == []


@pytest.mark.parametrize("severity", ["normal", "low"])
def test_retry_log_decisions_omit_non_urgent_failures(severity: str) -> None:
    decisions = build_urgent_alert_retry_log_decisions(
        [
            _dispatch_result(
                "telegram",
                severity=severity,
                status="failed",
                error_kind="timeout",
            )
        ]
    )

    assert decisions == []


def test_retry_log_decisions_classify_missing_error_kind_as_manual_check() -> None:
    decisions = build_urgent_alert_retry_log_decisions(
        [_dispatch_result("desktop", status="failed")]
    )

    assert decisions == [
        {
            "provider": "desktop",
            "severity": "urgent",
            "status": "failed",
            "requires_confirmation": True,
            "retry_action": "manual_check",
            "max_attempts": 0,
        }
    ]
    assert set(decisions[0]) == {
        "provider",
        "severity",
        "status",
        "requires_confirmation",
        "retry_action",
        "max_attempts",
    }


def test_retry_log_decisions_preserve_multiple_provider_order() -> None:
    decisions = build_urgent_alert_retry_log_decisions(
        [
            _dispatch_result("telegram", error_kind="timeout"),
            _dispatch_result("console", status="sent"),
            _dispatch_result(
                "desktop",
                status="skipped",
                error_kind="missing_dispatcher",
            ),
            _dispatch_result("file", error_kind="os_error"),
        ]
    )

    assert [decision["provider"] for decision in decisions] == [
        "telegram",
        "desktop",
        "file",
    ]
    assert [decision["retry_action"] for decision in decisions] == [
        "retry",
        "manual_check",
        "retry",
    ]


def test_retry_log_decisions_do_not_leak_unknown_or_private_fields() -> None:
    raw_result = {
        "provider": "telegram",
        "severity": "urgent",
        "status": "failed",
        "requires_confirmation": True,
        "error_kind": "http_error",
        "message": "raw transcript answer",
        "source_segment_ids": ["segment-secret"],
        "event_id": "event-secret",
        "session_id": "session-secret",
        "private_path": "C:\\Users\\student\\.env",
        "raw_audio": "C:\\Users\\student\\lecture.wav",
        "bot_token": "BOT_TOKEN=secret-token",
        "chat_id": "12345",
        "request_url": "https://api.telegram.example/bot-secret/sendMessage",
        "stdout": "provider stdout",
        "stderr": "provider stderr",
        "exception_text": "raw exception text",
        "auth_state": "browser auth data",
        "model_path": "C:\\models\\private-model",
    }

    decisions = build_urgent_alert_retry_log_decisions(
        [cast(AlertDispatchResult, raw_result)]
    )

    assert decisions == [
        {
            "provider": "telegram",
            "severity": "urgent",
            "status": "failed",
            "requires_confirmation": True,
            "error_kind": "http_error",
            "retry_action": "retry",
            "max_attempts": 3,
        }
    ]
    serialized = json.dumps(decisions)
    for leaked_string in [
        "raw transcript",
        "segment-secret",
        "event-secret",
        "session-secret",
        ".env",
        "lecture.wav",
        "secret-token",
        "12345",
        "sendMessage",
        "stdout",
        "stderr",
        "raw exception",
        "auth data",
        "private-model",
    ]:
        assert leaked_string not in serialized
