from __future__ import annotations

import inspect
import json

import pytest

from async_scholar import alert_routing_smoke
from async_scholar.alert_routing_smoke import (
    LOCAL_ALERT_ROUTING_SMOKE_ERROR,
    build_local_alert_routing_smoke,
)
from async_scholar.alerts import build_alert_notification_payload


def test_local_alert_routing_smoke_routes_known_event_through_dispatch_boundary() -> (
    None
):
    calls: list[object] = []

    def dispatcher(payload: object) -> dict[str, str]:
        calls.append(payload)
        return {"status": "sent", "raw": "provider internals stay out"}

    result = build_local_alert_routing_smoke(
        "attendance_prompt",
        dispatcher=dispatcher,
    )

    assert calls == [build_alert_notification_payload("attendance_prompt")]
    assert result == {
        "decision": "delivered",
        "delivery_performed": True,
        "error_kind": "none",
        "event_type_known": True,
        "provider": "local_console",
        "reason": "local_console_dispatch_succeeded",
        "requires_confirmation": True,
        "severity": "urgent",
        "smoke_kind": "local_alert_routing",
        "status": "sent",
    }
    assert set(result) == {
        "decision",
        "delivery_performed",
        "error_kind",
        "event_type_known",
        "provider",
        "reason",
        "requires_confirmation",
        "severity",
        "smoke_kind",
        "status",
    }


def test_local_alert_routing_smoke_disabled_does_not_call_dispatcher() -> None:
    def dispatcher(payload: object) -> dict[str, str]:
        raise AssertionError("disabled smoke must not call dispatcher")

    result = build_local_alert_routing_smoke(
        "attendance_prompt",
        disabled=True,
        dispatcher=dispatcher,
    )

    assert result == {
        "decision": "disabled",
        "delivery_performed": False,
        "error_kind": "none",
        "event_type_known": True,
        "provider": "local_console",
        "reason": "local_alert_routing_smoke_disabled",
        "requires_confirmation": True,
        "severity": "urgent",
        "smoke_kind": "local_alert_routing",
        "status": "skipped",
    }


def test_local_alert_routing_smoke_sanitizes_unknown_malicious_event_type() -> None:
    raw_event_type = (
        "future_event transcript_text source_segment_id=seg-1 "
        "C:\\Users\\student\\lecture.wav token=secret browser_cookie"
    )

    result = build_local_alert_routing_smoke(raw_event_type)

    assert result == {
        "decision": "delivered",
        "delivery_performed": True,
        "error_kind": "none",
        "event_type_known": False,
        "provider": "local_console",
        "reason": "local_console_dispatch_succeeded",
        "requires_confirmation": True,
        "severity": "normal",
        "smoke_kind": "local_alert_routing",
        "status": "sent",
    }
    serialized = json.dumps(result)
    for forbidden_fragment in (
        "future_event",
        "transcript_text",
        "source_segment_id",
        "C:\\Users",
        "student",
        "lecture.wav",
        "token",
        "secret",
        "browser_cookie",
    ):
        assert forbidden_fragment not in serialized


def test_local_alert_routing_smoke_sanitizes_dispatcher_failure() -> None:
    def dispatcher(payload: object) -> None:
        raise RuntimeError("BOT_TOKEN=secret C:\\Users\\student\\.env traceback")

    result = build_local_alert_routing_smoke(
        "quiz_prompt",
        dispatcher=dispatcher,
    )

    assert result == {
        "decision": "failed",
        "delivery_performed": False,
        "error_kind": "provider_error",
        "event_type_known": True,
        "provider": "local_console",
        "reason": "local_console_dispatch_failed",
        "requires_confirmation": True,
        "severity": "urgent",
        "smoke_kind": "local_alert_routing",
        "status": "failed",
    }
    serialized = json.dumps(result)
    for forbidden_fragment in (
        "BOT_TOKEN",
        "secret",
        "C:\\Users",
        ".env",
        "traceback",
    ):
        assert forbidden_fragment not in serialized


@pytest.mark.parametrize("event_type", ["", "   ", "attendance_prompt\nsecret"])
def test_local_alert_routing_smoke_rejects_unusable_event_type(
    event_type: str,
) -> None:
    with pytest.raises(ValueError, match=LOCAL_ALERT_ROUTING_SMOKE_ERROR):
        build_local_alert_routing_smoke(event_type)


def test_local_alert_routing_smoke_source_stays_local_and_dependency_free() -> None:
    source = inspect.getsource(alert_routing_smoke).lower()

    assert "dispatch_alert" in source
    for forbidden_fragment in (
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
        "vad",
        "stt",
        "mic",
        "loopback",
        "meeting",
        "browser",
        "auth",
        "profile",
        "cookie",
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
        assert forbidden_fragment not in source
