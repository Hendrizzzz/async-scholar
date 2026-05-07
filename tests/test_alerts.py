from __future__ import annotations

import pytest

from async_scholar.alerts import (
    build_alert_notification_payload,
    classify_alert_severity,
)


@pytest.mark.parametrize(
    ("event_type", "severity"),
    [
        ("attendance_prompt", "urgent"),
        ("name_call", "urgent"),
        ("camera_mic_request", "urgent"),
        ("quiz_prompt", "urgent"),
        ("direct_question", "normal"),
        ("task_prompt", "normal"),
        ("deadline_mention", "normal"),
        ("dismissal_cue", "low"),
    ],
)
def test_classify_alert_severity_maps_known_event_types(
    event_type: str,
    severity: str,
) -> None:
    assert classify_alert_severity(event_type) == severity


def test_classify_alert_severity_defaults_unknown_event_types_to_normal() -> None:
    assert classify_alert_severity("future_event_type") == "normal"


def test_build_alert_notification_payload_for_urgent_event() -> None:
    payload = build_alert_notification_payload("attendance_prompt")

    assert payload == {
        "severity": "urgent",
        "title": "Urgent: Attendance check",
        "body": "Review now; confirm before any participation action.",
        "requires_confirmation": True,
    }


def test_build_alert_notification_payload_for_normal_event() -> None:
    payload = build_alert_notification_payload("direct_question")

    assert payload == {
        "severity": "normal",
        "title": "Lecture alert: Direct question",
        "body": "Review when available; confirm before any participation action.",
        "requires_confirmation": True,
    }


def test_build_alert_notification_payload_for_low_event() -> None:
    payload = build_alert_notification_payload("dismissal_cue")

    assert payload == {
        "severity": "low",
        "title": "Low priority: Class wrap-up",
        "body": "Saved for review; confirm before any participation action.",
        "requires_confirmation": True,
    }


def test_build_alert_notification_payload_for_unknown_event_is_generic() -> None:
    unknown_event_type = (
        "future_event_type transcript_text segment-123 "
        "C:\\private\\lecture.wav token=secret"
    )

    payload = build_alert_notification_payload(unknown_event_type)

    assert payload == {
        "severity": "normal",
        "title": "Lecture alert: Lecture event",
        "body": "Review when available; confirm before any participation action.",
        "requires_confirmation": True,
    }
    payload_text = f"{payload['title']} {payload['body']}"
    assert "future_event_type" not in payload_text
    assert "transcript_text" not in payload_text
    assert "segment-123" not in payload_text
    assert "C:\\private\\lecture.wav" not in payload_text
    assert "secret" not in payload_text
