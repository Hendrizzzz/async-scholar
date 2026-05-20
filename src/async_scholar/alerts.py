"""Deterministic alert classification helpers."""

from __future__ import annotations

from typing import Literal, TextIO, TypedDict

AlertSeverity = Literal["low", "normal", "urgent"]


class AlertNotificationPayload(TypedDict):
    """JSON-ready notification content for later delivery adapters."""

    severity: AlertSeverity
    title: str
    body: str
    requires_confirmation: bool


_URGENT_EVENT_TYPES = frozenset(
    {
        "attendance_prompt",
        "name_call",
        "camera_mic_request",
        "quiz_prompt",
    }
)
_LOW_EVENT_TYPES = frozenset({"dismissal_cue"})

_EVENT_LABELS = {
    "attendance_prompt": "Attendance check",
    "name_call": "Name call",
    "camera_mic_request": "Camera or microphone request",
    "quiz_prompt": "Quiz prompt",
    "direct_question": "Direct question",
    "task_prompt": "Task instruction",
    "deadline_mention": "Deadline mention",
    "dismissal_cue": "Class wrap-up",
    "synthetic_session_awareness": "Synthetic session awareness",
}
_UNKNOWN_EVENT_LABEL = "Lecture event"

_SEVERITY_TITLE_PREFIXES: dict[AlertSeverity, str] = {
    "urgent": "Urgent",
    "normal": "Lecture alert",
    "low": "Low priority",
}
_SEVERITY_BODIES: dict[AlertSeverity, str] = {
    "urgent": "Review now; confirm before any participation action.",
    "normal": "Review when available; confirm before any participation action.",
    "low": "Saved for review; confirm before any participation action.",
}


def classify_alert_severity(event_type: str) -> AlertSeverity:
    """Classify known lecture event types into alert severity levels."""
    if event_type in _URGENT_EVENT_TYPES:
        return "urgent"
    if event_type in _LOW_EVENT_TYPES:
        return "low"
    return "normal"


def build_alert_notification_payload(event_type: str) -> AlertNotificationPayload:
    """Build privacy-safe notification content from controlled alert labels."""
    severity = classify_alert_severity(event_type)
    event_label = _EVENT_LABELS.get(event_type, _UNKNOWN_EVENT_LABEL)
    return {
        "severity": severity,
        "title": f"{_SEVERITY_TITLE_PREFIXES[severity]}: {event_label}",
        "body": _SEVERITY_BODIES[severity],
        "requires_confirmation": True,
    }


def write_console_alert_notification(
    event_type: str,
    stream: TextIO,
) -> AlertNotificationPayload:
    """Write one privacy-safe console notification line to a text stream."""
    payload = build_alert_notification_payload(event_type)
    stream.write(f"{payload['severity']} | {payload['title']} | {payload['body']}\n")
    return payload


__all__ = [
    "AlertNotificationPayload",
    "AlertSeverity",
    "build_alert_notification_payload",
    "classify_alert_severity",
    "write_console_alert_notification",
]
