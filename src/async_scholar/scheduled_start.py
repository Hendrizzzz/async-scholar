"""Non-executing scheduled-start plan models."""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import VERSION, BaseModel, ValidationError

from async_scholar.schedule_config import ScheduleConfig

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
SESSION_ID_MAX_LENGTH = 128
SOURCE_KIND_VALUES = ("file", "mic")
SCHEDULED_START_DECISION_KIND = "scheduled_start_due_decision"
SCHEDULED_START_MANUAL_RESULT_KIND = "scheduled_start_manual_result"
SCHEDULED_START_MANUAL_RESULT_ERROR = "scheduled start manual result could not be built"
SCHEDULED_START_NEXT_PREVIEW_ERROR = "scheduled start next preview could not be built"
SCHEDULED_START_DUE_LIST_ERROR = "scheduled start due list could not be built"
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
_SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_LOCAL_START_TIME_PATTERN = re.compile(r"^\d{2}:\d{2}$")
_DAY_OF_WEEK_SET = frozenset(DAY_OF_WEEK_VALUES)
_SOURCE_KIND_SET = frozenset(SOURCE_KIND_VALUES)
_WINDOWS_RESERVED_SESSION_NAMES = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{index}" for index in range(1, 10)),
        *(f"LPT{index}" for index in range(1, 10)),
    }
)
_MINUTES_PER_DAY = 24 * 60
_MINUTES_PER_WEEK = 7 * _MINUTES_PER_DAY

ScheduledStartPlanSummary = dict[str, str | int | bool | None]
ScheduledStartClockSummary = dict[str, str]
ScheduledStartDueDecisionSummary = dict[str, str | int | bool | None]
ScheduledStartManualResultSummary = dict[str, str | int | bool | None]
ScheduledStartNextPreviewSummary = dict[str, str | int | bool | None]
ScheduledStartDueListSummary = dict[str, object]


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


def _normalize_day_of_week_text(value: Any, *, field_name: str) -> str:
    normalized = _clean_required_text(
        value,
        field_name=field_name,
        max_length=max(len(day) for day in DAY_OF_WEEK_VALUES),
    ).lower()
    if normalized not in _DAY_OF_WEEK_SET:
        raise ValueError(f"{field_name} must be a full weekday name")
    return normalized


def _normalize_local_time_text(value: Any, *, field_name: str) -> str:
    normalized = _clean_required_text(
        value,
        field_name=field_name,
        max_length=5,
    )
    if _LOCAL_START_TIME_PATTERN.fullmatch(normalized) is None:
        raise ValueError(f"{field_name} must use HH:MM")

    hour_text, minute_text = normalized.split(":")
    hour = int(hour_text)
    minute = int(minute_text)
    if hour > 23 or minute > 59:
        raise ValueError(f"{field_name} must be a valid local time")
    return normalized


def _normalize_optional_day_of_week(value: Any, *, field_name: str) -> str | None:
    if value is None:
        return None
    return _normalize_day_of_week_text(value, field_name=field_name)


def _normalize_optional_local_time(value: Any, *, field_name: str) -> str | None:
    if value is None:
        return None
    return _normalize_local_time_text(value, field_name=field_name)


def _normalize_session_id(value: Any) -> str:
    if type(value) is not str:
        raise ValueError("session_id is invalid")
    if value != value.strip() or not value:
        raise ValueError("session_id is invalid")
    if len(value) > SESSION_ID_MAX_LENGTH:
        raise ValueError("session_id is invalid")
    if _has_control_character(value):
        raise ValueError("session_id is invalid")
    if "/" in value or "\\" in value:
        raise ValueError("session_id is invalid")
    if ":" in value or "://" in value:
        raise ValueError("session_id is invalid")
    if ".." in value:
        raise ValueError("session_id is invalid")
    if _SESSION_ID_PATTERN.fullmatch(value) is None:
        raise ValueError("session_id is invalid")
    reserved_candidate = value.split(".", maxsplit=1)[0].upper()
    if reserved_candidate in _WINDOWS_RESERVED_SESSION_NAMES:
        raise ValueError("session_id is invalid")
    return value


def _normalize_selected_class_time_index(
    selected_class_time_index: Any,
    schedule_config: ScheduleConfig,
) -> int:
    if isinstance(selected_class_time_index, bool) or not isinstance(
        selected_class_time_index,
        int,
    ):
        raise ValueError("selected_class_time_index must be an integer")
    if selected_class_time_index < 0 or selected_class_time_index >= len(
        schedule_config.class_times
    ):
        raise ValueError("selected_class_time_index is out of range")
    return selected_class_time_index


class ScheduledStartClock(BaseModel):
    """Explicit local clock input for non-executing scheduler decisions."""

    day_of_week: str
    local_time: str

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
        return _normalize_day_of_week_text(value, field_name="day_of_week")

    @_before_validator("local_time")
    def _normalize_local_time(cls, value: Any) -> str:
        return _normalize_local_time_text(value, field_name="local_time")

    def to_json_ready(self) -> ScheduledStartClockSummary:
        """Return deterministic explicit-clock metadata."""

        return {
            "day_of_week": self.day_of_week,
            "local_time": self.local_time,
        }

    def to_safe_summary(self) -> ScheduledStartClockSummary:
        """Return explicit-clock metadata suitable for display or export."""

        return self.to_json_ready()

    def safe_summary(self) -> ScheduledStartClockSummary:
        """Alias for callers that need a concise safe display payload."""

        return self.to_json_ready()

    def to_safe_export(self) -> ScheduledStartClockSummary:
        """Return deterministic explicit-clock data without execution state."""

        return self.to_json_ready()


class ScheduledStartPlan(BaseModel):
    """Immutable plan metadata for a future local session start."""

    course_id: str
    day_of_week: str
    local_start_time: str
    duration_minutes: int
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
        return _normalize_day_of_week_text(value, field_name="day_of_week")

    @_before_validator("local_start_time")
    def _normalize_local_start_time(cls, value: Any) -> str:
        return _normalize_local_time_text(value, field_name="local_start_time")

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

    def to_safe_summary(self) -> ScheduledStartPlanSummary:
        """Return inert plan metadata suitable for display or export."""

        return {
            "course_id": self.course_id,
            "day_of_week": self.day_of_week,
            "local_start_time": self.local_start_time,
            "duration_minutes": self.duration_minutes,
            "timezone_name": self.timezone_name,
            "meeting_label": self.meeting_label,
            "source_kind": self.source_kind,
            "enabled": self.enabled,
        }

    def safe_summary(self) -> ScheduledStartPlanSummary:
        """Alias for callers that need a concise safe display payload."""

        return self.to_safe_summary()

    def to_safe_export(self) -> ScheduledStartPlanSummary:
        """Return deterministic plan data without execution state."""

        return self.to_safe_summary()


class ScheduledStartDueDecision(BaseModel):
    """Pure scheduler decision metadata with no execution side effects."""

    decision_kind: Literal["scheduled_start_due_decision"] = (
        SCHEDULED_START_DECISION_KIND
    )
    status: Literal["due", "waiting", "disabled"]
    course_id: str
    source_kind: str
    enabled: bool
    clock_day_of_week: str
    clock_local_time: str
    scheduled_day_of_week: str
    scheduled_local_start_time: str
    due: bool
    minutes_until_start: int | None
    next_day_of_week: str | None
    next_local_start_time: str | None

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

    @_before_validator("enabled", "due")
    def _normalize_boolean(cls, value: Any) -> bool:
        if not isinstance(value, bool):
            raise ValueError("decision flags must be boolean")
        return value

    @_before_validator("clock_day_of_week", "scheduled_day_of_week")
    def _normalize_decision_day_of_week(cls, value: Any) -> str:
        return _normalize_day_of_week_text(value, field_name="day_of_week")

    @_before_validator("clock_local_time", "scheduled_local_start_time")
    def _normalize_decision_local_time(cls, value: Any) -> str:
        return _normalize_local_time_text(value, field_name="local_time")

    @_before_validator("minutes_until_start")
    def _normalize_minutes_until_start(cls, value: Any) -> int | None:
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("minutes_until_start must be an integer")
        if value < 0 or value > _MINUTES_PER_WEEK:
            raise ValueError("minutes_until_start must be within one week")
        return value

    @_before_validator("next_day_of_week")
    def _normalize_next_day_of_week(cls, value: Any) -> str | None:
        return _normalize_optional_day_of_week(value, field_name="next_day_of_week")

    @_before_validator("next_local_start_time")
    def _normalize_next_local_start_time(cls, value: Any) -> str | None:
        return _normalize_optional_local_time(
            value,
            field_name="next_local_start_time",
        )

    def to_json_ready(self) -> ScheduledStartDueDecisionSummary:
        """Return deterministic due-decision metadata for safe serialization."""

        return {
            "decision_kind": self.decision_kind,
            "status": self.status,
            "course_id": self.course_id,
            "source_kind": self.source_kind,
            "enabled": self.enabled,
            "clock_day_of_week": self.clock_day_of_week,
            "clock_local_time": self.clock_local_time,
            "scheduled_day_of_week": self.scheduled_day_of_week,
            "scheduled_local_start_time": self.scheduled_local_start_time,
            "due": self.due,
            "minutes_until_start": self.minutes_until_start,
            "next_day_of_week": self.next_day_of_week,
            "next_local_start_time": self.next_local_start_time,
        }

    def to_safe_summary(self) -> ScheduledStartDueDecisionSummary:
        """Return due-decision metadata suitable for display or export."""

        return self.to_json_ready()

    def safe_summary(self) -> ScheduledStartDueDecisionSummary:
        """Alias for callers that need a concise safe display payload."""

        return self.to_json_ready()

    def to_safe_export(self) -> ScheduledStartDueDecisionSummary:
        """Return deterministic due-decision data without execution state."""

        return self.to_json_ready()


class ScheduledStartManualResult(BaseModel):
    """One-shot manual scheduler result metadata without side effects."""

    result_kind: Literal["scheduled_start_manual_result"] = (
        SCHEDULED_START_MANUAL_RESULT_KIND
    )
    status: Literal["due", "waiting", "disabled"]
    session_id: str
    course_id: str
    source_kind: str
    enabled: bool
    clock_day_of_week: str
    clock_local_time: str
    scheduled_day_of_week: str
    scheduled_local_start_time: str
    due: bool
    minutes_until_start: int | None
    next_day_of_week: str | None
    next_local_start_time: str | None

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

    @_before_validator("session_id")
    def _normalize_result_session_id(cls, value: Any) -> str:
        return _normalize_session_id(value)

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

    @_before_validator("enabled", "due")
    def _normalize_boolean(cls, value: Any) -> bool:
        if not isinstance(value, bool):
            raise ValueError("result flags must be boolean")
        return value

    @_before_validator("clock_day_of_week", "scheduled_day_of_week")
    def _normalize_result_day_of_week(cls, value: Any) -> str:
        return _normalize_day_of_week_text(value, field_name="day_of_week")

    @_before_validator("clock_local_time", "scheduled_local_start_time")
    def _normalize_result_local_time(cls, value: Any) -> str:
        return _normalize_local_time_text(value, field_name="local_time")

    @_before_validator("minutes_until_start")
    def _normalize_minutes_until_start(cls, value: Any) -> int | None:
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("minutes_until_start must be an integer")
        if value < 0 or value > _MINUTES_PER_WEEK:
            raise ValueError("minutes_until_start must be within one week")
        return value

    @_before_validator("next_day_of_week")
    def _normalize_next_day_of_week(cls, value: Any) -> str | None:
        return _normalize_optional_day_of_week(value, field_name="next_day_of_week")

    @_before_validator("next_local_start_time")
    def _normalize_next_local_start_time(cls, value: Any) -> str | None:
        return _normalize_optional_local_time(
            value,
            field_name="next_local_start_time",
        )

    def to_json_ready(self) -> ScheduledStartManualResultSummary:
        """Return deterministic one-shot scheduler metadata."""

        return _scheduled_start_manual_result_to_json_ready(
            _revalidate_scheduled_start_manual_result(self)
        )

    def to_safe_summary(self) -> ScheduledStartManualResultSummary:
        """Return one-shot scheduler metadata suitable for local display."""

        return self.to_json_ready()

    def safe_summary(self) -> ScheduledStartManualResultSummary:
        """Alias for callers that need a concise safe display payload."""

        return self.to_json_ready()

    def to_safe_export(self) -> ScheduledStartManualResultSummary:
        """Return deterministic one-shot scheduler data."""

        return self.to_json_ready()


def _model_to_primitive(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _revalidate_scheduled_start_plan(plan: ScheduledStartPlan) -> ScheduledStartPlan:
    try:
        return ScheduledStartPlan(**_model_to_primitive(plan))
    except (TypeError, ValidationError, ValueError):
        raise ValueError("scheduled start preflight input failed validation") from None


def _revalidate_scheduled_start_clock(
    clock: ScheduledStartClock,
) -> ScheduledStartClock:
    try:
        return ScheduledStartClock(**_model_to_primitive(clock))
    except (TypeError, ValidationError, ValueError):
        raise ValueError("scheduled start preflight input failed validation") from None


def _revalidate_scheduled_start_manual_result(
    result: ScheduledStartManualResult,
) -> ScheduledStartManualResult:
    if type(result) is not ScheduledStartManualResult:
        raise ValueError(SCHEDULED_START_MANUAL_RESULT_ERROR)
    try:
        return ScheduledStartManualResult(**_model_to_primitive(result))
    except (TypeError, ValidationError, ValueError):
        raise ValueError(SCHEDULED_START_MANUAL_RESULT_ERROR) from None


def _scheduled_start_manual_result_to_json_ready(
    result: ScheduledStartManualResult,
) -> ScheduledStartManualResultSummary:
    return {
        "result_kind": result.result_kind,
        "status": result.status,
        "session_id": result.session_id,
        "course_id": result.course_id,
        "source_kind": result.source_kind,
        "enabled": result.enabled,
        "clock_day_of_week": result.clock_day_of_week,
        "clock_local_time": result.clock_local_time,
        "scheduled_day_of_week": result.scheduled_day_of_week,
        "scheduled_local_start_time": result.scheduled_local_start_time,
        "due": result.due,
        "minutes_until_start": result.minutes_until_start,
        "next_day_of_week": result.next_day_of_week,
        "next_local_start_time": result.next_local_start_time,
    }


def _local_minutes(day_of_week: str, local_time: str) -> int:
    day_index = DAY_OF_WEEK_VALUES.index(day_of_week)
    hour_text, minute_text = local_time.split(":")
    return day_index * _MINUTES_PER_DAY + int(hour_text) * 60 + int(minute_text)


def build_scheduled_start_due_decision(
    plan: ScheduledStartPlan,
    clock: ScheduledStartClock,
) -> ScheduledStartDueDecision:
    """Build a deterministic non-executing due decision from explicit inputs."""

    if type(plan) is not ScheduledStartPlan:
        raise ValueError("plan must be a ScheduledStartPlan")
    if type(clock) is not ScheduledStartClock:
        raise ValueError("clock must be a ScheduledStartClock")

    safe_plan = _revalidate_scheduled_start_plan(plan)
    safe_clock = _revalidate_scheduled_start_clock(clock)

    scheduled_minutes = _local_minutes(
        safe_plan.day_of_week,
        safe_plan.local_start_time,
    )
    clock_minutes = _local_minutes(safe_clock.day_of_week, safe_clock.local_time)
    minutes_until_start = scheduled_minutes - clock_minutes
    if minutes_until_start < 0:
        minutes_until_start += _MINUTES_PER_WEEK

    due = safe_plan.enabled and minutes_until_start == 0
    if not safe_plan.enabled:
        status: Literal["due", "waiting", "disabled"] = "disabled"
        decision_minutes: int | None = None
        next_day_of_week = None
        next_local_start_time = None
    else:
        status = "due" if due else "waiting"
        decision_minutes = minutes_until_start
        next_day_of_week = safe_plan.day_of_week
        next_local_start_time = safe_plan.local_start_time

    return ScheduledStartDueDecision(
        status=status,
        course_id=safe_plan.course_id,
        source_kind=safe_plan.source_kind,
        enabled=safe_plan.enabled,
        clock_day_of_week=safe_clock.day_of_week,
        clock_local_time=safe_clock.local_time,
        scheduled_day_of_week=safe_plan.day_of_week,
        scheduled_local_start_time=safe_plan.local_start_time,
        due=due,
        minutes_until_start=decision_minutes,
        next_day_of_week=next_day_of_week,
        next_local_start_time=next_local_start_time,
    )


def build_scheduled_start_manual_result(
    plan: ScheduledStartPlan,
    clock: ScheduledStartClock,
    session_id: str,
) -> ScheduledStartManualResult:
    """Build one-shot manual scheduler metadata from explicit local inputs."""

    try:
        if type(plan) is not ScheduledStartPlan:
            raise ValueError(SCHEDULED_START_MANUAL_RESULT_ERROR)
        if type(clock) is not ScheduledStartClock:
            raise ValueError(SCHEDULED_START_MANUAL_RESULT_ERROR)
        safe_session_id = _normalize_session_id(session_id)
        decision = build_scheduled_start_due_decision(plan, clock)
        return ScheduledStartManualResult(
            status=decision.status,
            session_id=safe_session_id,
            course_id=decision.course_id,
            source_kind=decision.source_kind,
            enabled=decision.enabled,
            clock_day_of_week=decision.clock_day_of_week,
            clock_local_time=decision.clock_local_time,
            scheduled_day_of_week=decision.scheduled_day_of_week,
            scheduled_local_start_time=decision.scheduled_local_start_time,
            due=decision.due,
            minutes_until_start=decision.minutes_until_start,
            next_day_of_week=decision.next_day_of_week,
            next_local_start_time=decision.next_local_start_time,
        )
    except (TypeError, ValidationError, ValueError):
        raise ValueError(SCHEDULED_START_MANUAL_RESULT_ERROR) from None


def scheduled_start_manual_result_to_json_ready(
    result: ScheduledStartManualResult,
) -> ScheduledStartManualResultSummary:
    return _scheduled_start_manual_result_to_json_ready(
        _revalidate_scheduled_start_manual_result(result)
    )


def scheduled_start_manual_result_safe_summary(
    result: ScheduledStartManualResult,
) -> ScheduledStartManualResultSummary:
    return _scheduled_start_manual_result_to_json_ready(
        _revalidate_scheduled_start_manual_result(result)
    )


def _normalize_next_preview_source_kind(value: Any) -> str:
    normalized = _clean_required_text(
        value,
        field_name="source_kind",
        max_length=max(len(kind) for kind in SOURCE_KIND_VALUES),
    ).lower()
    if normalized not in _SOURCE_KIND_SET:
        raise ValueError(SCHEDULED_START_NEXT_PREVIEW_ERROR)
    return normalized


def _next_preview_summary_from_manual_result(
    result: ScheduledStartManualResult,
    selected_class_time_index: int,
) -> ScheduledStartNextPreviewSummary:
    payload = scheduled_start_manual_result_safe_summary(result)
    return {
        "status": payload["status"],
        "session_id": payload["session_id"],
        "course_id": payload["course_id"],
        "source_kind": payload["source_kind"],
        "clock_day_of_week": payload["clock_day_of_week"],
        "clock_local_time": payload["clock_local_time"],
        "selected_class_time_index": selected_class_time_index,
        "scheduled_day_of_week": payload["scheduled_day_of_week"],
        "scheduled_local_start_time": payload["scheduled_local_start_time"],
        "due": payload["due"],
        "minutes_until_start": payload["minutes_until_start"],
        "next_day_of_week": payload["next_day_of_week"],
        "next_local_start_time": payload["next_local_start_time"],
    }


def build_next_scheduled_start_preview_summary(
    schedule_config: ScheduleConfig,
    clock: ScheduledStartClock,
    session_id: str,
    source_kind: str,
    *,
    enabled: bool = True,
) -> ScheduledStartNextPreviewSummary:
    """Select the next inert stored class-time preview from explicit inputs."""

    try:
        if type(schedule_config) is not ScheduleConfig:
            raise ValueError(SCHEDULED_START_NEXT_PREVIEW_ERROR)
        if type(clock) is not ScheduledStartClock:
            raise ValueError(SCHEDULED_START_NEXT_PREVIEW_ERROR)
        if not isinstance(enabled, bool):
            raise ValueError(SCHEDULED_START_NEXT_PREVIEW_ERROR)

        safe_schedule_config = ScheduleConfig(**_model_to_primitive(schedule_config))
        safe_clock = _revalidate_scheduled_start_clock(clock)
        safe_session_id = _normalize_session_id(session_id)
        safe_source_kind = _normalize_next_preview_source_kind(source_kind)

        if not enabled:
            return {
                "status": "disabled",
                "session_id": safe_session_id,
                "course_id": safe_schedule_config.course_id,
                "source_kind": safe_source_kind,
                "clock_day_of_week": safe_clock.day_of_week,
                "clock_local_time": safe_clock.local_time,
                "selected_class_time_index": None,
                "scheduled_day_of_week": None,
                "scheduled_local_start_time": None,
                "due": False,
                "minutes_until_start": None,
                "next_day_of_week": None,
                "next_local_start_time": None,
            }

        selected: tuple[int, int, ScheduledStartManualResult] | None = None
        for index, _class_time in enumerate(safe_schedule_config.class_times):
            plan = build_scheduled_start_plan(
                safe_schedule_config,
                selected_class_time_index=index,
                source_kind=safe_source_kind,
                enabled=True,
            )
            result = build_scheduled_start_manual_result(
                plan,
                safe_clock,
                safe_session_id,
            )
            if result.minutes_until_start is None:
                raise ValueError(SCHEDULED_START_NEXT_PREVIEW_ERROR)
            candidate = (result.minutes_until_start, index, result)
            if selected is None or candidate[:2] < selected[:2]:
                selected = candidate

        if selected is None:
            raise ValueError(SCHEDULED_START_NEXT_PREVIEW_ERROR)
        _minutes_until_start, selected_index, selected_result = selected
        return _next_preview_summary_from_manual_result(
            selected_result,
            selected_class_time_index=selected_index,
        )
    except (TypeError, ValidationError, ValueError):
        raise ValueError(SCHEDULED_START_NEXT_PREVIEW_ERROR) from None


def build_scheduled_start_due_list_summary(
    stored_courses: dict[str, object],
    clock: ScheduledStartClock,
    session_id: str,
    source_kind: str,
    *,
    enabled: bool = True,
) -> ScheduledStartDueListSummary:
    """Build a due-only summary across stored course timing data."""

    try:
        if not isinstance(stored_courses, dict):
            raise ValueError(SCHEDULED_START_DUE_LIST_ERROR)
        if type(clock) is not ScheduledStartClock:
            raise ValueError(SCHEDULED_START_DUE_LIST_ERROR)
        if not isinstance(enabled, bool):
            raise ValueError(SCHEDULED_START_DUE_LIST_ERROR)

        safe_clock = _revalidate_scheduled_start_clock(clock)
        safe_session_id = _normalize_session_id(session_id)
        safe_source_kind = _normalize_next_preview_source_kind(source_kind)
        course_count = _normalize_due_list_course_count(stored_courses["course_count"])
        course_rows = _normalize_due_list_courses(stored_courses["courses"])
        if len(course_rows) != course_count:
            raise ValueError(SCHEDULED_START_DUE_LIST_ERROR)

        if not enabled:
            return _scheduled_start_due_list_summary(
                status="disabled",
                session_id=safe_session_id,
                source_kind=safe_source_kind,
                clock=safe_clock,
                course_count=course_count,
                courses=[],
            )

        due_courses: list[dict[str, object]] = []
        for course_row in course_rows:
            preview = build_next_scheduled_start_preview_summary(
                _schedule_config_from_due_list_course(course_row),
                safe_clock,
                safe_session_id,
                safe_source_kind,
                enabled=True,
            )
            if preview["due"] is not True:
                continue

            selected_index = preview["selected_class_time_index"]
            if isinstance(selected_index, bool) or not isinstance(
                selected_index,
                int,
            ):
                raise ValueError(SCHEDULED_START_DUE_LIST_ERROR)
            class_times = course_row["class_times"]
            if not isinstance(class_times, list):
                raise ValueError(SCHEDULED_START_DUE_LIST_ERROR)
            selected_class_time = class_times[selected_index]
            if not isinstance(selected_class_time, dict):
                raise ValueError(SCHEDULED_START_DUE_LIST_ERROR)
            due_courses.append(
                {
                    "course_id": preview["course_id"],
                    "selected_class_time_index": selected_class_time[
                        "selected_class_time_index"
                    ],
                    "scheduled_day_of_week": preview["scheduled_day_of_week"],
                    "scheduled_local_start_time": preview["scheduled_local_start_time"],
                    "due": True,
                    "minutes_until_start": preview["minutes_until_start"],
                }
            )

        due_courses.sort(key=lambda course: str(course["course_id"]))
        return _scheduled_start_due_list_summary(
            status="due" if due_courses else "waiting",
            session_id=safe_session_id,
            source_kind=safe_source_kind,
            clock=safe_clock,
            course_count=course_count,
            courses=due_courses,
        )
    except (KeyError, IndexError, TypeError, ValidationError, ValueError):
        raise ValueError(SCHEDULED_START_DUE_LIST_ERROR) from None


def _scheduled_start_due_list_summary(
    *,
    status: Literal["due", "waiting", "disabled"],
    session_id: str,
    source_kind: str,
    clock: ScheduledStartClock,
    course_count: int,
    courses: list[dict[str, object]],
) -> ScheduledStartDueListSummary:
    return {
        "status": status,
        "session_id": session_id,
        "source_kind": source_kind,
        "clock_day_of_week": clock.day_of_week,
        "clock_local_time": clock.local_time,
        "course_count": course_count,
        "due_count": len(courses),
        "courses": courses,
    }


def _normalize_due_list_course_count(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(SCHEDULED_START_DUE_LIST_ERROR)
    return value


def _normalize_due_list_courses(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise ValueError(SCHEDULED_START_DUE_LIST_ERROR)
    course_ids: set[str] = set()
    courses: list[dict[str, object]] = []
    for course in value:
        if not isinstance(course, dict):
            raise ValueError(SCHEDULED_START_DUE_LIST_ERROR)
        course_id = _normalize_due_list_course_id(course["course_id"])
        if course_id in course_ids:
            raise ValueError(SCHEDULED_START_DUE_LIST_ERROR)
        course_ids.add(course_id)
        class_times = _normalize_due_list_class_times(course["class_times"])
        courses.append(
            {
                "course_id": course_id,
                "class_times": class_times,
            }
        )
    return courses


def _normalize_due_list_course_id(value: object) -> str:
    normalized = _clean_required_text(
        value,
        field_name="course_id",
        max_length=COURSE_ID_MAX_LENGTH,
    ).lower()
    if _COURSE_ID_PATTERN.fullmatch(normalized) is None:
        raise ValueError(SCHEDULED_START_DUE_LIST_ERROR)
    return normalized


def _normalize_due_list_class_times(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list) or not value:
        raise ValueError(SCHEDULED_START_DUE_LIST_ERROR)
    class_times: list[dict[str, object]] = []
    for class_time in value:
        if not isinstance(class_time, dict):
            raise ValueError(SCHEDULED_START_DUE_LIST_ERROR)
        selected_class_time_index = _normalize_due_list_selected_class_time_index(
            class_time["selected_class_time_index"]
        )
        class_times.append(
            {
                "selected_class_time_index": selected_class_time_index,
                "scheduled_day_of_week": _normalize_day_of_week_text(
                    class_time["scheduled_day_of_week"],
                    field_name="scheduled_day_of_week",
                ),
                "scheduled_local_start_time": _normalize_local_time_text(
                    class_time["scheduled_local_start_time"],
                    field_name="scheduled_local_start_time",
                ),
            }
        )
    return class_times


def _normalize_due_list_selected_class_time_index(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(SCHEDULED_START_DUE_LIST_ERROR)
    return value


def _schedule_config_from_due_list_course(
    course: dict[str, object],
) -> ScheduleConfig:
    class_times = course["class_times"]
    if not isinstance(class_times, list):
        raise ValueError(SCHEDULED_START_DUE_LIST_ERROR)
    return ScheduleConfig(
        course_id=course["course_id"],
        class_times=[
            {
                "day_of_week": class_time["scheduled_day_of_week"],
                "local_start_time": class_time["scheduled_local_start_time"],
                "duration_minutes": 1,
            }
            for class_time in class_times
            if isinstance(class_time, dict)
        ],
    )


def build_scheduled_start_plan(
    schedule_config: ScheduleConfig,
    selected_class_time_index: int,
    source_kind: str,
    *,
    enabled: bool = True,
) -> ScheduledStartPlan:
    """Build an inert plan from one configured weekly class window."""

    if not isinstance(schedule_config, ScheduleConfig):
        raise ValueError("schedule_config must be a ScheduleConfig")

    normalized_index = _normalize_selected_class_time_index(
        selected_class_time_index,
        schedule_config,
    )
    selected_class_time = schedule_config.class_times[normalized_index]

    return ScheduledStartPlan(
        course_id=schedule_config.course_id,
        day_of_week=selected_class_time.day_of_week,
        local_start_time=selected_class_time.local_start_time,
        duration_minutes=selected_class_time.duration_minutes,
        timezone_name=selected_class_time.timezone_name,
        meeting_label=selected_class_time.meeting_label,
        source_kind=source_kind,
        enabled=enabled,
    )
