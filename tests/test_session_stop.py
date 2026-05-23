import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from async_scholar import session_stop
from async_scholar.scheduled_start import ScheduledStartPlan
from async_scholar.session_stop import (
    STOP_AFTER_MINUTES_MAX,
    STORED_SESSION_STOP_PREVIEW_ERROR,
    SessionStopPlan,
    build_session_stop_plan,
    build_session_stop_preview_from_store_input,
)


def _model_dump(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _scheduled_start_plan(
    *,
    source_kind: str = "file",
    duration_minutes: int = 75,
    enabled: bool = True,
) -> ScheduledStartPlan:
    return ScheduledStartPlan(
        course_id=" CS_101 ",
        day_of_week=" Monday ",
        local_start_time=" 09:00 ",
        duration_minutes=duration_minutes,
        timezone_name=" Asia/Manila ",
        meeting_label=" Lecture ",
        source_kind=source_kind,
        enabled=enabled,
    )


def test_builds_valid_file_session_stop_plan() -> None:
    plan = SessionStopPlan(
        course_id=" CS_101 ",
        day_of_week=" Monday ",
        local_start_time=" 09:00 ",
        stop_after_minutes=75,
        timezone_name=" Asia/Manila ",
        meeting_label=" Lecture ",
        source_kind=" File ",
    )

    assert plan == SessionStopPlan(
        course_id="cs_101",
        day_of_week="monday",
        local_start_time="09:00",
        stop_after_minutes=75,
        timezone_name="Asia/Manila",
        meeting_label="Lecture",
        source_kind="file",
        enabled=True,
    )


def test_builds_valid_mic_session_stop_plan() -> None:
    plan = SessionStopPlan(
        course_id="cs101",
        day_of_week="THURSDAY",
        local_start_time="\t18:45\n",
        stop_after_minutes=105,
        timezone_name=" ",
        meeting_label="\t",
        source_kind="mic",
        enabled=False,
    )

    assert plan.course_id == "cs101"
    assert plan.day_of_week == "thursday"
    assert plan.local_start_time == "18:45"
    assert plan.stop_after_minutes == 105
    assert plan.timezone_name is None
    assert plan.meeting_label is None
    assert plan.source_kind == "mic"
    assert plan.enabled is False


def test_build_session_stop_plan_from_scheduled_start_plan() -> None:
    plan = build_session_stop_plan(
        _scheduled_start_plan(source_kind="mic", duration_minutes=105, enabled=False)
    )

    assert plan == SessionStopPlan(
        course_id="cs_101",
        day_of_week="monday",
        local_start_time="09:00",
        stop_after_minutes=105,
        timezone_name="Asia/Manila",
        meeting_label="Lecture",
        source_kind="mic",
        enabled=False,
    )


@pytest.mark.parametrize("source_kind", ["", "   ", "browser", "audio", "camera", 1])
def test_session_stop_plan_rejects_invalid_source_kinds(
    source_kind: object,
) -> None:
    with pytest.raises(ValidationError):
        SessionStopPlan(
            course_id="cs101",
            day_of_week="monday",
            local_start_time="09:00",
            stop_after_minutes=60,
            source_kind=source_kind,
        )


@pytest.mark.parametrize(
    "stop_after_minutes",
    [0, -1, STOP_AFTER_MINUTES_MAX + 1, 90.5, "90", True],
)
def test_session_stop_plan_rejects_invalid_stop_durations(
    stop_after_minutes: object,
) -> None:
    with pytest.raises(ValidationError):
        SessionStopPlan(
            course_id="cs101",
            day_of_week="monday",
            local_start_time="09:00",
            stop_after_minutes=stop_after_minutes,
            source_kind="file",
        )


@pytest.mark.parametrize("scheduled_start_plan", [{"course_id": "cs101"}, object()])
def test_build_session_stop_plan_rejects_non_scheduled_start_inputs(
    scheduled_start_plan: object,
) -> None:
    with pytest.raises(ValueError):
        build_session_stop_plan(scheduled_start_plan)


def test_session_stop_plan_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        SessionStopPlan(
            course_id="cs101",
            day_of_week="monday",
            local_start_time="09:00",
            stop_after_minutes=60,
            source_kind="file",
            meeting_url="https://meet.example.edu/private",
        )

    with pytest.raises(ValidationError):
        SessionStopPlan(
            course_id="cs101",
            day_of_week="monday",
            local_start_time="09:00",
            stop_after_minutes=60,
            source_kind="mic",
            timer_state="running",
        )


@pytest.mark.parametrize("enabled", ["yes", 1, None])
def test_session_stop_plan_rejects_non_boolean_enabled_values(
    enabled: object,
) -> None:
    with pytest.raises(ValidationError):
        SessionStopPlan(
            course_id="cs101",
            day_of_week="monday",
            local_start_time="09:00",
            stop_after_minutes=60,
            source_kind="file",
            enabled=enabled,
        )


def test_session_stop_plan_is_immutable() -> None:
    plan = build_session_stop_plan(_scheduled_start_plan())

    with pytest.raises((TypeError, ValidationError)):
        plan.enabled = False


def test_session_stop_plan_safe_summary_and_export_contents() -> None:
    plan = build_session_stop_plan(_scheduled_start_plan())

    expected = {
        "course_id": "cs_101",
        "day_of_week": "monday",
        "local_start_time": "09:00",
        "stop_after_minutes": 75,
        "timezone_name": "Asia/Manila",
        "meeting_label": "Lecture",
        "source_kind": "file",
        "enabled": True,
    }

    assert plan.to_safe_summary() == expected
    assert plan.safe_summary() == expected
    assert plan.to_safe_export() == expected

    summary_text = str(expected).lower()
    for forbidden_text in [
        "meeting_url",
        "file_path",
        "device_id",
        "secret",
        "auth",
        "profile",
        "recording",
        "transcript",
        "archive",
        "artifact",
        "next_run",
        "timer",
        "worker",
        "scheduler",
    ]:
        assert forbidden_text not in summary_text


def test_session_stop_plan_uses_json_ready_pydantic_serialization() -> None:
    plan = build_session_stop_plan(
        _scheduled_start_plan(source_kind="mic", duration_minutes=105, enabled=False)
    )

    serialized = json.loads(json.dumps(_model_dump(plan), sort_keys=True))

    assert serialized == {
        "course_id": "cs_101",
        "day_of_week": "monday",
        "local_start_time": "09:00",
        "stop_after_minutes": 105,
        "timezone_name": "Asia/Manila",
        "meeting_label": "Lecture",
        "source_kind": "mic",
        "enabled": False,
    }


def test_build_session_stop_preview_from_store_input_is_allowlisted() -> None:
    summary = build_session_stop_preview_from_store_input(
        {
            "course_id": " CS_101 ",
            "selected_class_time_index": 1,
            "scheduled_day_of_week": " Wednesday ",
            "scheduled_local_start_time": " 13:30 ",
            "stop_after_minutes": 90,
            "title": "Confidential Systems",
            "meeting_url": "https://meet.example.edu/token-secret",
        },
        " Mic ",
    )

    assert summary == {
        "status": "enabled",
        "course_id": "cs_101",
        "source_kind": "mic",
        "selected_class_time_index": 1,
        "scheduled_day_of_week": "wednesday",
        "scheduled_local_start_time": "13:30",
        "stop_after_minutes": 90,
        "enabled": True,
    }
    assert list(summary) == [
        "status",
        "course_id",
        "source_kind",
        "selected_class_time_index",
        "scheduled_day_of_week",
        "scheduled_local_start_time",
        "stop_after_minutes",
        "enabled",
    ]
    public_text = str(summary).lower()
    for forbidden_fragment in (
        "title",
        "meeting",
        "meet.example",
        "token",
        "secret",
        "timezone",
        "instructor",
        "transcript",
        "audio",
        "browser",
    ):
        assert forbidden_fragment not in public_text


def test_build_session_stop_preview_from_store_input_supports_disabled() -> None:
    summary = build_session_stop_preview_from_store_input(
        {
            "course_id": "cs101",
            "selected_class_time_index": 0,
            "scheduled_day_of_week": "monday",
            "scheduled_local_start_time": "09:00",
            "stop_after_minutes": 75,
        },
        "file",
        enabled=False,
    )

    assert summary == {
        "status": "disabled",
        "course_id": "cs101",
        "source_kind": "file",
        "selected_class_time_index": 0,
        "scheduled_day_of_week": "monday",
        "scheduled_local_start_time": "09:00",
        "stop_after_minutes": 75,
        "enabled": False,
    }


@pytest.mark.parametrize(
    ("stored_class_time", "source_kind", "enabled"),
    [
        ({}, "file", True),
        (
            {
                "course_id": "cs101",
                "selected_class_time_index": -1,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "stop_after_minutes": 75,
            },
            "file",
            True,
        ),
        (
            {
                "course_id": "cs101",
                "selected_class_time_index": 0,
                "scheduled_day_of_week": "notaday",
                "scheduled_local_start_time": "09:00",
                "stop_after_minutes": 75,
            },
            "file",
            True,
        ),
        (
            {
                "course_id": "cs101",
                "selected_class_time_index": 0,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "99:99",
                "stop_after_minutes": 75,
            },
            "file",
            True,
        ),
        (
            {
                "course_id": "cs101",
                "selected_class_time_index": 0,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "stop_after_minutes": 0,
            },
            "file",
            True,
        ),
        (
            {
                "course_id": "cs101",
                "selected_class_time_index": 0,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "stop_after_minutes": 75,
            },
            "browser",
            True,
        ),
        (
            {
                "course_id": "cs101",
                "selected_class_time_index": 0,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "stop_after_minutes": 75,
            },
            "file",
            "yes",
        ),
    ],
)
def test_build_session_stop_preview_from_store_input_sanitizes_failures(
    stored_class_time: dict[str, object],
    source_kind: str,
    enabled: object,
) -> None:
    with pytest.raises(ValueError) as exc_info:
        build_session_stop_preview_from_store_input(
            stored_class_time,
            source_kind,
            enabled=enabled,
        )

    assert str(exc_info.value) == STORED_SESSION_STOP_PREVIEW_ERROR
    for forbidden_fragment in (
        "notaday",
        "99:99",
        "browser",
        "traceback",
    ):
        assert forbidden_fragment not in str(exc_info.value).lower()


def test_session_stop_module_has_no_execution_or_private_behavior() -> None:
    source = Path(session_stop.__file__).read_text(encoding="utf-8")

    forbidden_tokens = [
        "sqlite",
        "jsonl",
        "open(",
        "read_text",
        "write_text",
        "playwright",
        "selenium",
        "nicegui",
        "requests",
        "httpx",
        "aiohttp",
        "fastapi",
        "asyncio",
        "threading",
        "subprocess",
        "zoneinfo",
        "datetime",
        "timedelta",
        "sleep(",
        "timer",
        "cron",
        "apscheduler",
        "webbrowser",
        "google",
        "fixturesessionworker",
        "fixturesessionlifecyclecontroller",
        "sounddevice",
        "vad",
        "stt",
        "file_transcription",
        "device_id",
        "meeting_url",
        "file_path",
        "recording_path",
        "transcript_path",
        "archive_path",
        "artifact_path",
        "next_run",
    ]

    normalized_source = source.lower()
    for forbidden_token in forbidden_tokens:
        assert forbidden_token not in normalized_source
