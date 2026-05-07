from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs

import pytest

from async_scholar import telegram_notifier


class FakeResponse:
    def __init__(self, status: int = 200) -> None:
        self.status = status
        self.closed = False

    def close(self) -> None:
        self.closed = True


def test_dispatch_telegram_alert_notification_sends_controlled_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "severity": "urgent",
        "title": "Attendance prompt",
        "body": "Please answer the poll.",
        "requires_confirmation": True,
    }
    builder_calls: list[str] = []

    def fake_builder(event_type: str) -> dict[str, object]:
        builder_calls.append(event_type)
        return payload

    captured: dict[str, object] = {}
    fake_response = FakeResponse(status=200)

    def fake_opener(request, timeout=None):
        captured["request"] = request
        captured["timeout"] = timeout
        return fake_response

    monkeypatch.setattr(
        telegram_notifier,
        "build_alert_notification_payload",
        fake_builder,
    )

    result = telegram_notifier.dispatch_telegram_alert_notification(
        "attendance_prompt",
        bot_token="123456:ABCDEF",
        chat_id=987654321,
        opener=fake_opener,
        timeout=7.5,
    )

    assert builder_calls == ["attendance_prompt"]
    assert result == {
        "provider": "telegram",
        "severity": "urgent",
        "title": "Attendance prompt",
        "body": "Please answer the poll.",
        "requires_confirmation": True,
        "ok": True,
        "status": "sent",
        "http_status": 200,
    }
    assert fake_response.closed is True
    assert captured["timeout"] == 7.5

    request = captured["request"]
    assert request.get_method() == "POST"
    form = parse_qs(request.data.decode("utf-8"))
    assert form["chat_id"] == ["987654321"]
    assert form["text"] == ["urgent | Attendance prompt | Please answer the poll."]

    result_json = json.dumps(result, sort_keys=True)
    assert "123456:ABCDEF" not in result_json
    assert "987654321" not in result_json
    assert "https://api.telegram.org" not in result_json


@pytest.mark.parametrize(
    ("bot_token", "chat_id", "missing_fields"),
    [
        (None, 12345, ["bot_token"]),
        ("  ", "67890", ["bot_token"]),
        ("123456:ABCDEF", None, ["chat_id"]),
        ("123456:ABCDEF", "   ", ["chat_id"]),
    ],
)
def test_dispatch_telegram_alert_notification_missing_credentials_skips_transport(
    monkeypatch: pytest.MonkeyPatch,
    bot_token,
    chat_id,
    missing_fields,
) -> None:
    payload = {
        "severity": "normal",
        "title": "Lecture event",
        "body": "Check the room.",
        "requires_confirmation": True,
    }
    builder_calls: list[str] = []
    transport_called = False

    def fake_builder(event_type: str) -> dict[str, object]:
        builder_calls.append(event_type)
        return payload

    def fake_opener(request, timeout=None):  # pragma: no cover - defensive
        nonlocal transport_called
        transport_called = True
        raise AssertionError("transport should not be called for missing credentials")

    monkeypatch.setattr(
        telegram_notifier,
        "build_alert_notification_payload",
        fake_builder,
    )

    result = telegram_notifier.dispatch_telegram_alert_notification(
        "attendance_prompt",
        bot_token=bot_token,
        chat_id=chat_id,
        opener=fake_opener,
    )

    assert builder_calls == ["attendance_prompt"]
    assert transport_called is False
    assert result == {
        "provider": "telegram",
        "severity": "normal",
        "title": "Lecture event",
        "body": "Check the room.",
        "requires_confirmation": True,
        "ok": False,
        "status": "failed",
        "error_kind": "missing_credentials",
        "missing_fields": missing_fields,
    }


def test_dispatch_telegram_alert_notification_http_error_is_sanitized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "severity": "low",
        "title": "Dismissal cue",
        "body": "Wrap up the activity.",
        "requires_confirmation": True,
    }

    def fake_builder(event_type: str) -> dict[str, object]:
        return payload

    def fake_opener(request, timeout=None):
        raise HTTPError(
            request.full_url,
            403,
            "Forbidden",
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr(
        telegram_notifier,
        "build_alert_notification_payload",
        fake_builder,
    )

    result = telegram_notifier.dispatch_telegram_alert_notification(
        "dismissal_cue",
        bot_token="123456:ABCDEF",
        chat_id="987654321",
        opener=fake_opener,
    )

    assert result == {
        "provider": "telegram",
        "severity": "low",
        "title": "Dismissal cue",
        "body": "Wrap up the activity.",
        "requires_confirmation": True,
        "ok": False,
        "status": "failed",
        "error_kind": "http_error",
        "http_status": 403,
    }
    result_json = json.dumps(result, sort_keys=True)
    assert "Forbidden" not in result_json
    assert "123456:ABCDEF" not in result_json


@pytest.mark.parametrize(
    ("raised", "expected_error_kind"),
    [
        (TimeoutError("timed out"), "timeout"),
        (URLError(TimeoutError("timed out")), "timeout"),
        (OSError("network unreachable"), "network_error"),
    ],
)
def test_dispatch_telegram_alert_notification_timeout_and_network_errors_are_sanitized(
    monkeypatch: pytest.MonkeyPatch,
    raised: Exception,
    expected_error_kind: str,
) -> None:
    payload = {
        "severity": "normal",
        "title": "Lecture event",
        "body": "Check the room.",
        "requires_confirmation": True,
    }

    def fake_builder(event_type: str) -> dict[str, object]:
        return payload

    def fake_opener(request, timeout=None):
        raise raised

    monkeypatch.setattr(
        telegram_notifier,
        "build_alert_notification_payload",
        fake_builder,
    )

    result = telegram_notifier.dispatch_telegram_alert_notification(
        "attendance_prompt",
        bot_token="123456:ABCDEF",
        chat_id="987654321",
        opener=fake_opener,
    )

    assert result == {
        "provider": "telegram",
        "severity": "normal",
        "title": "Lecture event",
        "body": "Check the room.",
        "requires_confirmation": True,
        "ok": False,
        "status": "failed",
        "error_kind": expected_error_kind,
    }
    result_json = json.dumps(result, sort_keys=True)
    assert "timed out" not in result_json
    assert "network unreachable" not in result_json


def test_dispatch_telegram_alert_notification_unknown_event_type_is_not_echoed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    suspicious_event_type = (
        "attendance_prompt /tmp/private/transcript.jsonl "
        "source-segment-7 session-123 .env token auth browser model"
    )
    payload = {
        "severity": "normal",
        "title": "Lecture event",
        "body": "Check the room.",
        "requires_confirmation": True,
    }
    builder_calls: list[str] = []
    captured: dict[str, object] = {}

    def fake_builder(event_type: str) -> dict[str, object]:
        builder_calls.append(event_type)
        return payload

    def fake_opener(request, timeout=None):
        captured["request"] = request
        captured["body"] = request.data.decode("utf-8")
        return FakeResponse(status=200)

    monkeypatch.setattr(
        telegram_notifier,
        "build_alert_notification_payload",
        fake_builder,
    )

    result = telegram_notifier.dispatch_telegram_alert_notification(
        suspicious_event_type,
        bot_token="123456:ABCDEF",
        chat_id="987654321",
        opener=fake_opener,
    )

    assert builder_calls == [suspicious_event_type]
    assert result["ok"] is True
    assert result["status"] == "sent"
    assert "http_status" in result and result["http_status"] == 200
    assert suspicious_event_type not in captured["body"]

    result_json = json.dumps(result, sort_keys=True)
    assert suspicious_event_type not in result_json
    assert "private/transcript.jsonl" not in result_json
    assert ".env" not in result_json
    assert "auth browser model" not in result_json
