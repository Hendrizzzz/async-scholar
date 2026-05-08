import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from async_scholar import scheduled_start
from async_scholar.schedule_config import ScheduleConfig
from async_scholar.scheduled_start import (
    ScheduledStartPlan,
    build_scheduled_start_plan,
)


def _model_dump(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _schedule_config() -> ScheduleConfig:
    return ScheduleConfig(
        course_id=" CS_101 ",
        class_times=[
            {
                "day_of_week": " Monday ",
                "local_start_time": " 09:00 ",
                "duration_minutes": 75,
                "timezone_name": " Asia/Manila ",
                "meeting_label": " Lecture ",
            },
            {
                "day_of_week": " THURSDAY ",
                "local_start_time": "\t18:45\n",
                "duration_minutes": 105,
                "timezone_name": " ",
                "meeting_label": "\t",
            },
        ],
    )


def test_builds_valid_file_scheduled_start_plan_from_schedule_config() -> None:
    plan = build_scheduled_start_plan(
        _schedule_config(),
        selected_class_time_index=0,
        source_kind=" File ",
    )

    assert plan == ScheduledStartPlan(
        course_id="cs_101",
        day_of_week="monday",
        local_start_time="09:00",
        duration_minutes=75,
        timezone_name="Asia/Manila",
        meeting_label="Lecture",
        source_kind="file",
        enabled=True,
    )


def test_builds_valid_mic_scheduled_start_plan_from_selected_class_time() -> None:
    plan = build_scheduled_start_plan(
        _schedule_config(),
        selected_class_time_index=1,
        source_kind="mic",
        enabled=False,
    )

    assert plan.course_id == "cs_101"
    assert plan.day_of_week == "thursday"
    assert plan.local_start_time == "18:45"
    assert plan.duration_minutes == 105
    assert plan.timezone_name is None
    assert plan.meeting_label is None
    assert plan.source_kind == "mic"
    assert plan.enabled is False


@pytest.mark.parametrize("source_kind", ["", "   ", "browser", "audio", "camera", 1])
def test_scheduled_start_plan_rejects_invalid_source_kinds(
    source_kind: object,
) -> None:
    with pytest.raises(ValidationError):
        ScheduledStartPlan(
            course_id="cs101",
            day_of_week="monday",
            local_start_time="09:00",
            duration_minutes=60,
            source_kind=source_kind,
        )


@pytest.mark.parametrize("selected_class_time_index", [-1, 2, True, "0", 0.5])
def test_build_scheduled_start_plan_rejects_invalid_class_time_indexes(
    selected_class_time_index: object,
) -> None:
    with pytest.raises(ValueError):
        build_scheduled_start_plan(
            _schedule_config(),
            selected_class_time_index=selected_class_time_index,
            source_kind="file",
        )


def test_build_scheduled_start_plan_rejects_non_schedule_config_inputs() -> None:
    with pytest.raises(ValueError):
        build_scheduled_start_plan(
            {"course_id": "cs101"},
            selected_class_time_index=0,
            source_kind="file",
        )


def test_scheduled_start_plan_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ScheduledStartPlan(
            course_id="cs101",
            day_of_week="monday",
            local_start_time="09:00",
            duration_minutes=60,
            source_kind="file",
            meeting_url="https://meet.example.edu/private",
        )


def test_scheduled_start_plan_rejects_non_boolean_enabled_values() -> None:
    with pytest.raises(ValidationError):
        ScheduledStartPlan(
            course_id="cs101",
            day_of_week="monday",
            local_start_time="09:00",
            duration_minutes=60,
            source_kind="file",
            enabled="yes",
        )


def test_scheduled_start_plan_is_immutable() -> None:
    plan = build_scheduled_start_plan(
        _schedule_config(),
        selected_class_time_index=0,
        source_kind="file",
    )

    with pytest.raises((TypeError, ValidationError)):
        plan.enabled = False


def test_scheduled_start_plan_safe_summary_and_export_contents() -> None:
    plan = build_scheduled_start_plan(
        _schedule_config(),
        selected_class_time_index=0,
        source_kind="file",
    )

    expected = {
        "course_id": "cs_101",
        "day_of_week": "monday",
        "local_start_time": "09:00",
        "duration_minutes": 75,
        "timezone_name": "Asia/Manila",
        "meeting_label": "Lecture",
        "source_kind": "file",
        "enabled": True,
    }

    assert plan.to_safe_summary() == expected
    assert plan.safe_summary() == expected
    assert plan.to_safe_export() == expected

    summary_text = str(expected)
    for forbidden_text in [
        "meeting_url",
        "secret",
        "auth",
        "profile",
        "recording",
        "transcript",
        "archive",
        "artifact",
        "path",
        "device",
        "next_run",
        "timer",
        "worker",
    ]:
        assert forbidden_text not in summary_text


def test_scheduled_start_plan_uses_json_ready_pydantic_serialization() -> None:
    plan = build_scheduled_start_plan(
        _schedule_config(),
        selected_class_time_index=1,
        source_kind="mic",
        enabled=False,
    )

    serialized = json.loads(json.dumps(_model_dump(plan), sort_keys=True))

    assert serialized == {
        "course_id": "cs_101",
        "day_of_week": "thursday",
        "local_start_time": "18:45",
        "duration_minutes": 105,
        "timezone_name": None,
        "meeting_label": None,
        "source_kind": "mic",
        "enabled": False,
    }


def test_scheduled_start_module_has_no_execution_or_private_behavior() -> None:
    source = Path(scheduled_start.__file__).read_text(encoding="utf-8")

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
        "recording_path",
        "transcript_path",
        "archive_path",
        "artifact_path",
        "next_run",
    ]

    normalized_source = source.lower()
    for forbidden_token in forbidden_tokens:
        assert forbidden_token not in normalized_source
