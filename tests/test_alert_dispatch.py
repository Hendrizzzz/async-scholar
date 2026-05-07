from __future__ import annotations

import json

from async_scholar.alert_dispatch import dispatch_alert
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
