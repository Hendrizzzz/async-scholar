"""Deterministic alert classification helpers."""

from __future__ import annotations

from typing import Literal

AlertSeverity = Literal["low", "normal", "urgent"]

_URGENT_EVENT_TYPES = frozenset(
    {
        "attendance_prompt",
        "name_call",
        "camera_mic_request",
        "quiz_prompt",
    }
)
_LOW_EVENT_TYPES = frozenset({"dismissal_cue"})


def classify_alert_severity(event_type: str) -> AlertSeverity:
    """Classify known lecture event types into alert severity levels."""
    if event_type in _URGENT_EVENT_TYPES:
        return "urgent"
    if event_type in _LOW_EVENT_TYPES:
        return "low"
    return "normal"


__all__ = ["AlertSeverity", "classify_alert_severity"]
