"""Non-executing session-stop plan models."""

from __future__ import annotations

import re
from typing import Any

from pydantic import VERSION, BaseModel, ValidationError

from async_scholar.scheduled_start import ScheduledStartPlan

if VERSION.startswith("2."):
    from pydantic import ConfigDict, field_validator

    _PYDANTIC_V2 = True
else:
    from pydantic import validator

    _PYDANTIC_V2 = False


COURSE_ID_MAX_LENGTH = 64
OPTIONAL_TEXT_MAX_LENGTH = 120
TIMEZONE_NAME_MAX_LENGTH = 64
STOP_AFTER_MINUTES_MAX = 24 * 60
SOURCE_KIND_VALUES = ("file", "mic")
STORED_SESSION_STOP_PREVIEW_ERROR = "stored session stop preview could not be built"
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
_SOURCE_KIND_SET = frozenset(SOURCE_KIND_VALUES)

SessionStopPlanSummary = dict[str, str | int | bool | None]
StoredSessionStopPreviewSummary = dict[str, str | int | bool]


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


class SessionStopPlan(BaseModel):
    """Immutable plan metadata for a future local session stop."""

    course_id: str
    day_of_week: str
    local_start_time: str
    stop_after_minutes: int
    timezone_name: str | None = None
    meeting_label: str | None = None
    source_kind: str
    enabled: bool = True

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

    @_before_validator("stop_after_minutes")
    def _normalize_stop_after_minutes(cls, value: Any) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("stop_after_minutes must be an integer")
        if value <= 0 or value > STOP_AFTER_MINUTES_MAX:
            raise ValueError("stop_after_minutes must be positive and bounded")
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

    @_before_validator("source_kind")
    def _normalize_source_kind(cls, value: Any) -> str:
        normalized = _clean_required_text(
            value,
            field_name="source_kind",
            max_length=max(len(kind) for kind in SOURCE_KIND_VALUES),
        ).lower()
        if normalized not in _SOURCE_KIND_SET:
            raise ValueError("source_kind must be file or mic")
        return normalized

    @_before_validator("enabled")
    def _normalize_enabled(cls, value: Any) -> bool:
        if not isinstance(value, bool):
            raise ValueError("enabled must be a boolean")
        return value

    def to_safe_summary(self) -> SessionStopPlanSummary:
        """Return inert plan metadata suitable for display or export."""

        return {
            "course_id": self.course_id,
            "day_of_week": self.day_of_week,
            "local_start_time": self.local_start_time,
            "stop_after_minutes": self.stop_after_minutes,
            "timezone_name": self.timezone_name,
            "meeting_label": self.meeting_label,
            "source_kind": self.source_kind,
            "enabled": self.enabled,
        }

    def safe_summary(self) -> SessionStopPlanSummary:
        """Alias for callers that need a concise safe display payload."""

        return self.to_safe_summary()

    def to_safe_export(self) -> SessionStopPlanSummary:
        """Return deterministic plan data without execution state."""

        return self.to_safe_summary()


def build_session_stop_plan(
    scheduled_start_plan: ScheduledStartPlan,
) -> SessionStopPlan:
    """Build an inert stop plan from one configured local session start."""

    if not isinstance(scheduled_start_plan, ScheduledStartPlan):
        raise ValueError("scheduled_start_plan must be a ScheduledStartPlan")

    return SessionStopPlan(
        course_id=scheduled_start_plan.course_id,
        day_of_week=scheduled_start_plan.day_of_week,
        local_start_time=scheduled_start_plan.local_start_time,
        stop_after_minutes=scheduled_start_plan.duration_minutes,
        timezone_name=scheduled_start_plan.timezone_name,
        meeting_label=scheduled_start_plan.meeting_label,
        source_kind=scheduled_start_plan.source_kind,
        enabled=scheduled_start_plan.enabled,
    )


def build_session_stop_preview_from_store_input(
    stored_class_time: dict[str, object],
    source_kind: str,
    *,
    enabled: bool = True,
) -> StoredSessionStopPreviewSummary:
    """Build inert session-stop preview metadata from one stored class time."""

    try:
        selected_class_time_index = _clean_selected_class_time_index(
            stored_class_time["selected_class_time_index"]
        )
        plan = SessionStopPlan(
            course_id=stored_class_time["course_id"],
            day_of_week=stored_class_time["scheduled_day_of_week"],
            local_start_time=stored_class_time["scheduled_local_start_time"],
            stop_after_minutes=stored_class_time["stop_after_minutes"],
            source_kind=source_kind,
            enabled=enabled,
        )
    except (KeyError, TypeError, ValidationError, ValueError):
        raise ValueError(STORED_SESSION_STOP_PREVIEW_ERROR) from None

    return {
        "status": "enabled" if plan.enabled else "disabled",
        "course_id": plan.course_id,
        "source_kind": plan.source_kind,
        "selected_class_time_index": selected_class_time_index,
        "scheduled_day_of_week": plan.day_of_week,
        "scheduled_local_start_time": plan.local_start_time,
        "stop_after_minutes": plan.stop_after_minutes,
        "enabled": plan.enabled,
    }


def _clean_selected_class_time_index(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("selected_class_time_index must be a non-negative integer")
    return value
