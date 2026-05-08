import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from async_scholar import schedule_config
from async_scholar.schedule_config import (
    DURATION_MINUTES_MAX,
    OPTIONAL_TEXT_MAX_LENGTH,
    TIMEZONE_NAME_MAX_LENGTH,
    ScheduleConfig,
    WeeklyClassTime,
)


def _model_dump(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def test_schedule_config_valid_creation_and_immutability() -> None:
    class_time = WeeklyClassTime(
        day_of_week="monday",
        local_start_time="09:30",
        duration_minutes=90,
        timezone_name="Asia/Manila",
        meeting_label="Lecture room",
    )
    config = ScheduleConfig(course_id="cs101", class_times=[class_time])

    assert config.course_id == "cs101"
    assert config.class_times == (class_time,)
    assert class_time.day_of_week == "monday"
    assert class_time.local_start_time == "09:30"
    assert class_time.duration_minutes == 90
    assert class_time.timezone_name == "Asia/Manila"
    assert class_time.meeting_label == "Lecture room"

    with pytest.raises((TypeError, ValidationError)):
        config.course_id = "changed"

    with pytest.raises((TypeError, ValidationError)):
        class_time.duration_minutes = 30


def test_schedule_config_supports_multiple_class_times() -> None:
    config = ScheduleConfig(
        course_id="cs101",
        class_times=[
            {
                "day_of_week": "monday",
                "local_start_time": "09:00",
                "duration_minutes": 75,
            },
            {
                "day_of_week": "wednesday",
                "local_start_time": "13:30",
                "duration_minutes": 120,
                "timezone_name": "Asia/Manila",
                "meeting_label": "Lab",
            },
        ],
    )

    assert len(config.class_times) == 2
    assert config.class_times[0].day_of_week == "monday"
    assert config.class_times[1].day_of_week == "wednesday"
    assert config.class_times[1].meeting_label == "Lab"


def test_schedule_config_normalizes_whitespace_and_case() -> None:
    config = ScheduleConfig(
        course_id=" CS_101 ",
        class_times=[
            {
                "day_of_week": " TUESDAY ",
                "local_start_time": "\t08:05\n",
                "duration_minutes": 45,
                "timezone_name": " Asia/Manila ",
                "meeting_label": " Lecture hall ",
            },
            {
                "day_of_week": " friday ",
                "local_start_time": " 16:00 ",
                "duration_minutes": 60,
                "timezone_name": " ",
                "meeting_label": "\t",
            },
        ],
    )

    first, second = config.class_times

    assert config.course_id == "cs_101"
    assert first.day_of_week == "tuesday"
    assert first.local_start_time == "08:05"
    assert first.timezone_name == "Asia/Manila"
    assert first.meeting_label == "Lecture hall"
    assert second.day_of_week == "friday"
    assert second.local_start_time == "16:00"
    assert second.timezone_name is None
    assert second.meeting_label is None


@pytest.mark.parametrize(
    "course_id",
    ["", "   ", "bad id", "-bad", "bad!", "a" * 65],
)
def test_schedule_config_rejects_invalid_or_blank_course_ids(course_id: str) -> None:
    with pytest.raises(ValidationError):
        ScheduleConfig(
            course_id=course_id,
            class_times=[
                {
                    "day_of_week": "monday",
                    "local_start_time": "09:00",
                    "duration_minutes": 60,
                }
            ],
        )


@pytest.mark.parametrize("day_of_week", ["", "   ", "mon", "funday", 1])
def test_weekly_class_time_rejects_invalid_day_values(day_of_week: object) -> None:
    with pytest.raises(ValidationError):
        WeeklyClassTime(
            day_of_week=day_of_week,
            local_start_time="09:00",
            duration_minutes=60,
        )


@pytest.mark.parametrize(
    "local_start_time",
    ["", "   ", "9:00", "24:00", "12:60", "12:00:00", "aa:bb", 900],
)
def test_weekly_class_time_rejects_invalid_local_start_times(
    local_start_time: object,
) -> None:
    with pytest.raises(ValidationError):
        WeeklyClassTime(
            day_of_week="monday",
            local_start_time=local_start_time,
            duration_minutes=60,
        )


@pytest.mark.parametrize(
    "duration_minutes",
    [0, -1, DURATION_MINUTES_MAX + 1, 90.5, "90", True],
)
def test_weekly_class_time_rejects_invalid_duration_values(
    duration_minutes: object,
) -> None:
    with pytest.raises(ValidationError):
        WeeklyClassTime(
            day_of_week="monday",
            local_start_time="09:00",
            duration_minutes=duration_minutes,
        )


@pytest.mark.parametrize(
    ("field_name", "max_length"),
    [
        ("timezone_name", TIMEZONE_NAME_MAX_LENGTH),
        ("meeting_label", OPTIONAL_TEXT_MAX_LENGTH),
    ],
)
def test_weekly_class_time_rejects_invalid_optional_text(
    field_name: str,
    max_length: int,
) -> None:
    with pytest.raises(ValidationError):
        WeeklyClassTime(
            day_of_week="monday",
            local_start_time="09:00",
            duration_minutes=60,
            **{field_name: "x" * (max_length + 1)},
        )

    with pytest.raises(ValidationError):
        WeeklyClassTime(
            day_of_week="monday",
            local_start_time="09:00",
            duration_minutes=60,
            **{field_name: "line\nbreak"},
        )


def test_schedule_config_rejects_missing_or_empty_class_times() -> None:
    with pytest.raises(ValidationError):
        ScheduleConfig(course_id="cs101", class_times=[])

    with pytest.raises(ValidationError):
        ScheduleConfig(course_id="cs101", class_times=None)


def test_schedule_config_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        WeeklyClassTime(
            day_of_week="monday",
            local_start_time="09:00",
            duration_minutes=60,
            meeting_url="https://meet.example.edu/private",
        )

    with pytest.raises(ValidationError):
        ScheduleConfig(
            course_id="cs101",
            class_times=[
                {
                    "day_of_week": "monday",
                    "local_start_time": "09:00",
                    "duration_minutes": 60,
                }
            ],
            next_run_time="2026-05-08T09:00:00",
        )


def test_schedule_config_safe_summary_and_export_contents() -> None:
    config = ScheduleConfig(
        course_id="cs101",
        class_times=[
            {
                "day_of_week": "monday",
                "local_start_time": "09:00",
                "duration_minutes": 60,
                "timezone_name": "Asia/Manila",
                "meeting_label": "Lecture",
            }
        ],
    )

    expected = {
        "course_id": "cs101",
        "class_times": [
            {
                "day_of_week": "monday",
                "local_start_time": "09:00",
                "duration_minutes": 60,
                "timezone_name": "Asia/Manila",
                "meeting_label": "Lecture",
            }
        ],
    }

    assert config.to_safe_summary() == expected
    assert config.safe_summary() == expected
    assert config.to_safe_export() == expected
    assert config.class_times[0].to_safe_export() == expected["class_times"][0]

    summary_text = str(expected)
    for forbidden_text in [
        "meeting_url",
        "secret",
        "auth",
        "profile",
        "recording",
        "transcript",
        "archive",
        "next_run",
    ]:
        assert forbidden_text not in summary_text


def test_schedule_config_uses_json_ready_pydantic_serialization() -> None:
    config = ScheduleConfig(
        course_id="CS101",
        class_times=[
            {
                "day_of_week": "Thursday",
                "local_start_time": "18:45",
                "duration_minutes": 105,
                "timezone_name": "Asia/Manila",
                "meeting_label": "Review",
            }
        ],
    )

    serialized = json.loads(json.dumps(_model_dump(config), sort_keys=True))

    assert serialized == {
        "course_id": "cs101",
        "class_times": [
            {
                "day_of_week": "thursday",
                "local_start_time": "18:45",
                "duration_minutes": 105,
                "timezone_name": "Asia/Manila",
                "meeting_label": "Review",
            }
        ],
    }


def test_schedule_config_module_has_no_persistence_scheduler_or_browser_behavior() -> (
    None
):
    source = Path(schedule_config.__file__).read_text(encoding="utf-8")

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
    ]

    normalized_source = source.lower()
    for forbidden_token in forbidden_tokens:
        assert forbidden_token not in normalized_source
