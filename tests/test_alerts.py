from __future__ import annotations

import pytest

from async_scholar.alerts import classify_alert_severity


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
