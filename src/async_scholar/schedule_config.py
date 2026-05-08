"""Class-time configuration models for manually entered course schedules."""

from __future__ import annotations

import re
from typing import Any

from pydantic import VERSION, BaseModel

if VERSION.startswith("2."):
    from pydantic import ConfigDict, field_validator

    _PYDANTIC_V2 = True
else:
    from pydantic import validator

    _PYDANTIC_V2 = False


COURSE_ID_MAX_LENGTH = 64
OPTIONAL_TEXT_MAX_LENGTH = 120
TIMEZONE_NAME_MAX_LENGTH = 64
DURATION_MINUTES_MAX = 24 * 60
DAY_OF_WEEK_VALUES = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)

_COURSE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_LOCAL_START_TIME_PATTERN = re.compile(r"^\d{2}:\d{2}$")
_DAY_OF_WEEK_SET = frozenset(DAY_OF_WEEK_VALUES)


WeeklyClassTimeSummary = dict[str, str | int | None]
ScheduleConfigSummary = dict[str, str | list[WeeklyClassTimeSummary]]


def _before_validator(*field_names: str) -> Any:
    if _PYDANTIC_V2:
        return field_validator(*field_names, mode="before")
    return validator(*field_names, pre=True, allow_reuse=True)


def _clean_required_text(value: Any, *, field_name: str, max_length: int) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} is required")
    if len(normalized) > max_length:
        raise ValueError(f"{field_name} is too long")
    return normalized


def _has_control_character(value: str) -> bool:
    return any(ord(char) < 0x20 or ord(char) == 0x7F for char in value)


def _clean_optional_text(value: Any, *, field_name: str, max_length: int) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")

    normalized = value.strip()
    if not normalized:
        return None
    if len(normalized) > max_length:
        raise ValueError(f"{field_name} is too long")
    if _has_control_character(normalized):
        raise ValueError(f"{field_name} contains unsupported characters")
    return normalized


class WeeklyClassTime(BaseModel):
    """Immutable weekly class window supplied by the user."""

    day_of_week: str
    local_start_time: str
    duration_minutes: int
    timezone_name: str | None = None
    meeting_label: str | None = None

    if _PYDANTIC_V2:
        model_config = ConfigDict(
            extra="forbid",
            frozen=True,
            hide_input_in_errors=True,
        )
    else:

        class Config:
            extra = "forbid"
            frozen = True

    @_before_validator("day_of_week")
    def _normalize_day_of_week(cls, value: Any) -> str:
        normalized = _clean_required_text(
            value,
            field_name="day_of_week",
            max_length=max(len(day) for day in DAY_OF_WEEK_VALUES),
        ).lower()
        if normalized not in _DAY_OF_WEEK_SET:
            raise ValueError("day_of_week must be a full weekday name")
        return normalized

    @_before_validator("local_start_time")
    def _normalize_local_start_time(cls, value: Any) -> str:
        normalized = _clean_required_text(
            value,
            field_name="local_start_time",
            max_length=5,
        )
        if _LOCAL_START_TIME_PATTERN.fullmatch(normalized) is None:
            raise ValueError("local_start_time must use HH:MM")

        hour_text, minute_text = normalized.split(":")
        hour = int(hour_text)
        minute = int(minute_text)
        if hour > 23 or minute > 59:
            raise ValueError("local_start_time must be a valid local time")
        return normalized

    @_before_validator("duration_minutes")
    def _normalize_duration_minutes(cls, value: Any) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("duration_minutes must be an integer")
        if value <= 0 or value > DURATION_MINUTES_MAX:
            raise ValueError("duration_minutes must be positive and bounded")
        return value

    @_before_validator("timezone_name")
    def _normalize_timezone_name(cls, value: Any) -> str | None:
        return _clean_optional_text(
            value,
            field_name="timezone_name",
            max_length=TIMEZONE_NAME_MAX_LENGTH,
        )

    @_before_validator("meeting_label")
    def _normalize_meeting_label(cls, value: Any) -> str | None:
        return _clean_optional_text(
            value,
            field_name="meeting_label",
            max_length=OPTIONAL_TEXT_MAX_LENGTH,
        )

    def to_safe_summary(self) -> WeeklyClassTimeSummary:
        """Return class-time metadata suitable for display or export."""

        return {
            "day_of_week": self.day_of_week,
            "local_start_time": self.local_start_time,
            "duration_minutes": self.duration_minutes,
            "timezone_name": self.timezone_name,
            "meeting_label": self.meeting_label,
        }

    def safe_summary(self) -> WeeklyClassTimeSummary:
        """Alias for callers that need a concise safe display payload."""

        return self.to_safe_summary()

    def to_safe_export(self) -> WeeklyClassTimeSummary:
        """Return deterministic class-time data for safe local export."""

        return self.to_safe_summary()


class ScheduleConfig(BaseModel):
    """Immutable weekly class schedule for one course."""

    course_id: str
    class_times: tuple[WeeklyClassTime, ...]

    if _PYDANTIC_V2:
        model_config = ConfigDict(
            extra="forbid",
            frozen=True,
            hide_input_in_errors=True,
        )
    else:

        class Config:
            extra = "forbid"
            frozen = True

    @_before_validator("course_id")
    def _normalize_course_id(cls, value: Any) -> str:
        normalized = _clean_required_text(
            value,
            field_name="course_id",
            max_length=COURSE_ID_MAX_LENGTH,
        ).lower()
        if _COURSE_ID_PATTERN.fullmatch(normalized) is None:
            raise ValueError(
                "course_id must use letters, numbers, hyphens, or underscores"
            )
        return normalized

    @_before_validator("class_times")
    def _normalize_class_times(cls, value: Any) -> tuple[Any, ...]:
        if value is None or isinstance(value, (str, bytes, dict)):
            raise ValueError("class_times must contain weekly class windows")

        try:
            normalized = tuple(value)
        except TypeError as exc:
            raise ValueError("class_times must contain weekly class windows") from exc

        if not normalized:
            raise ValueError("class_times must contain at least one class window")
        return normalized

    def to_safe_summary(self) -> ScheduleConfigSummary:
        """Return non-sensitive schedule metadata for display or export."""

        return {
            "course_id": self.course_id,
            "class_times": [
                class_time.to_safe_summary() for class_time in self.class_times
            ],
        }

    def safe_summary(self) -> ScheduleConfigSummary:
        """Alias for callers that need a concise safe display payload."""

        return self.to_safe_summary()

    def to_safe_export(self) -> ScheduleConfigSummary:
        """Return deterministic schedule data without execution state."""

        return self.to_safe_summary()
