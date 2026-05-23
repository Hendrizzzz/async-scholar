"""Pure stored session-window confirmation response model."""

from __future__ import annotations

import re

STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR = (
    "stored session window confirmation response could not be built"
)

StoredSessionWindowConfirmationResponseSummary = dict[str, object]

_CONFIRMATION_RESPONSE_TOKENS = frozenset(("confirmed", "declined"))
_PREFLIGHT_STATUSES = frozenset(("required", "not_required", "disabled"))
_RESPONSE_STATUSES = frozenset(("confirmed", "declined", "not_required", "disabled"))
_SOURCE_KINDS = frozenset(("file", "mic"))
_DAYS_OF_WEEK = frozenset(
    (
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    )
)
_SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_COURSE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_LOCAL_TIME_PATTERN = re.compile(r"^\d{2}:\d{2}$")
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
_PREFLIGHT_KEYS = (
    "status",
    "session_id",
    "source_kind",
    "clock_day_of_week",
    "clock_local_time",
    "course_count",
    "due_count",
    "ready_to_start",
    "confirmation_required",
    "confirmation_status",
    "blocked_execution_count",
    "courses",
)
_PREFLIGHT_COURSE_KEYS = (
    "course_id",
    "selected_class_time_index",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "due",
    "minutes_until_start",
    "stop_after_minutes",
    "enabled",
    "requires_confirmation",
)
_RESPONSE_KEYS = (
    "status",
    "session_id",
    "source_kind",
    "clock_day_of_week",
    "clock_local_time",
    "course_count",
    "due_count",
    "ready_to_start",
    "confirmation_required",
    "confirmation_status",
    "confirmation_response",
    "confirmation_verified",
    "confirmed_start_count",
    "blocked_execution_count",
    "courses",
)
_RESPONSE_COURSE_KEYS = (
    "course_id",
    "selected_class_time_index",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "due",
    "minutes_until_start",
    "stop_after_minutes",
    "enabled",
    "requires_confirmation",
    "confirmation_response",
)


def build_session_window_confirmation_response_summary(
    preflight_summary: dict[str, object],
    confirmation_response: str,
) -> StoredSessionWindowConfirmationResponseSummary:
    """Record a fixed human response against Ticket 146 preflight metadata."""

    try:
        safe_preflight = _preflight_safe_summary(preflight_summary)
        safe_response = _confirmation_response_token(confirmation_response)

        confirmation_required = _bool_value(safe_preflight["confirmation_required"])
        ready_to_start = _bool_value(safe_preflight["ready_to_start"])
        due_count = _non_negative_int(safe_preflight["due_count"])
        preflight_status = _preflight_status(safe_preflight["confirmation_status"])

        if preflight_status == "disabled":
            status = "disabled"
            confirmation_verified = False
            confirmed_start_count = 0
            blocked_execution_count = 0
            courses: list[dict[str, object]] = []
        elif not confirmation_required:
            status = "not_required"
            confirmation_verified = False
            confirmed_start_count = 0
            blocked_execution_count = 0
            courses = []
        elif ready_to_start and due_count > 0 and safe_response == "confirmed":
            status = "confirmed"
            confirmation_verified = True
            confirmed_start_count = due_count
            blocked_execution_count = 0
            courses = [
                {**course, "confirmation_response": safe_response}
                for course in _preflight_courses(safe_preflight["courses"])
            ]
        elif ready_to_start and due_count > 0 and safe_response == "declined":
            status = "declined"
            confirmation_verified = False
            confirmed_start_count = 0
            blocked_execution_count = due_count
            courses = [
                {**course, "confirmation_response": safe_response}
                for course in _preflight_courses(safe_preflight["courses"])
            ]
        else:
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)

        return session_window_confirmation_response_safe_summary(
            {
                "status": status,
                "session_id": safe_preflight["session_id"],
                "source_kind": safe_preflight["source_kind"],
                "clock_day_of_week": safe_preflight["clock_day_of_week"],
                "clock_local_time": safe_preflight["clock_local_time"],
                "course_count": safe_preflight["course_count"],
                "due_count": due_count,
                "ready_to_start": ready_to_start,
                "confirmation_required": confirmation_required,
                "confirmation_status": preflight_status,
                "confirmation_response": safe_response,
                "confirmation_verified": confirmation_verified,
                "confirmed_start_count": confirmed_start_count,
                "blocked_execution_count": blocked_execution_count,
                "courses": courses,
            }
        )
    except (KeyError, TypeError, ValueError):
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR) from None


def session_window_confirmation_response_safe_summary(
    payload: dict[str, object],
) -> StoredSessionWindowConfirmationResponseSummary:
    """Return only the Ticket 147 allowlisted JSON-safe fields."""

    try:
        if not isinstance(payload, dict):
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
        courses = payload["courses"]
        if not isinstance(courses, list):
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)

        safe_payload = {key: payload[key] for key in _RESPONSE_KEYS}
        status = _response_status(safe_payload["status"])
        confirmation_status = _preflight_status(safe_payload["confirmation_status"])
        confirmation_response = _confirmation_response_token(
            safe_payload["confirmation_response"]
        )
        due_count = _non_negative_int(safe_payload["due_count"])
        ready_to_start = _bool_value(safe_payload["ready_to_start"])
        confirmation_required = _bool_value(safe_payload["confirmation_required"])
        confirmation_verified = _bool_value(safe_payload["confirmation_verified"])
        confirmed_start_count = _non_negative_int(safe_payload["confirmed_start_count"])
        blocked_execution_count = _non_negative_int(
            safe_payload["blocked_execution_count"]
        )

        safe_payload["status"] = status
        safe_payload["session_id"] = _safe_session_id(safe_payload["session_id"])
        safe_payload["source_kind"] = _source_kind(safe_payload["source_kind"])
        safe_payload["clock_day_of_week"] = _day_of_week(
            safe_payload["clock_day_of_week"]
        )
        safe_payload["clock_local_time"] = _local_time(safe_payload["clock_local_time"])
        safe_payload["course_count"] = _non_negative_int(safe_payload["course_count"])
        safe_payload["due_count"] = due_count
        safe_payload["ready_to_start"] = ready_to_start
        safe_payload["confirmation_required"] = confirmation_required
        safe_payload["confirmation_status"] = confirmation_status
        safe_payload["confirmation_response"] = confirmation_response
        safe_payload["confirmation_verified"] = confirmation_verified
        safe_payload["confirmed_start_count"] = confirmed_start_count
        safe_payload["blocked_execution_count"] = blocked_execution_count

        _validate_response_policy(
            status=status,
            confirmation_status=confirmation_status,
            confirmation_response=confirmation_response,
            due_count=due_count,
            ready_to_start=ready_to_start,
            confirmation_required=confirmation_required,
            confirmation_verified=confirmation_verified,
            confirmed_start_count=confirmed_start_count,
            blocked_execution_count=blocked_execution_count,
            courses=courses,
        )
        safe_payload["courses"] = _response_courses(courses, confirmation_response)
        if (
            status in ("confirmed", "declined")
            and len(safe_payload["courses"]) != due_count
        ):
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
        return safe_payload
    except (KeyError, TypeError, ValueError):
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR) from None


def _preflight_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    if not isinstance(payload, dict) or set(payload) != set(_PREFLIGHT_KEYS):
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
    courses = payload["courses"]
    if not isinstance(courses, list):
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)

    safe_payload = {key: payload[key] for key in _PREFLIGHT_KEYS}
    status = _preflight_status(safe_payload["status"])
    confirmation_status = _preflight_status(safe_payload["confirmation_status"])
    if status != confirmation_status:
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)

    due_count = _non_negative_int(safe_payload["due_count"])
    ready_to_start = _bool_value(safe_payload["ready_to_start"])
    confirmation_required = _bool_value(safe_payload["confirmation_required"])
    blocked_execution_count = _non_negative_int(safe_payload["blocked_execution_count"])
    safe_payload["session_id"] = _safe_session_id(safe_payload["session_id"])
    safe_payload["source_kind"] = _source_kind(safe_payload["source_kind"])
    safe_payload["clock_day_of_week"] = _day_of_week(safe_payload["clock_day_of_week"])
    safe_payload["clock_local_time"] = _local_time(safe_payload["clock_local_time"])
    safe_payload["course_count"] = _non_negative_int(safe_payload["course_count"])
    safe_payload["due_count"] = due_count
    safe_payload["ready_to_start"] = ready_to_start
    safe_payload["confirmation_required"] = confirmation_required
    safe_payload["confirmation_status"] = confirmation_status
    safe_payload["blocked_execution_count"] = blocked_execution_count

    if confirmation_status in ("disabled", "not_required"):
        if ready_to_start or confirmation_required or due_count != 0:
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
        if blocked_execution_count != 0 or courses:
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
    else:
        if not ready_to_start or not confirmation_required or due_count <= 0:
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
        if blocked_execution_count != due_count:
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
        safe_courses = _preflight_courses(courses)
        if len(safe_courses) != due_count:
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
        safe_payload["courses"] = safe_courses
        return safe_payload

    safe_payload["courses"] = []
    return safe_payload


def _preflight_courses(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
    courses = [_preflight_course_safe_summary(course) for course in value]
    _ensure_unique_sorted_courses(courses)
    courses.sort(
        key=lambda course: (
            str(course["course_id"]),
            int(course["selected_class_time_index"]),
        )
    )
    return courses


def _preflight_course_safe_summary(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict) or set(payload) != set(_PREFLIGHT_COURSE_KEYS):
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
    safe_course = {key: payload[key] for key in _PREFLIGHT_COURSE_KEYS}
    safe_course["course_id"] = _safe_course_id(safe_course["course_id"])
    safe_course["selected_class_time_index"] = _non_negative_int(
        safe_course["selected_class_time_index"]
    )
    safe_course["scheduled_day_of_week"] = _day_of_week(
        safe_course["scheduled_day_of_week"]
    )
    safe_course["scheduled_local_start_time"] = _local_time(
        safe_course["scheduled_local_start_time"]
    )
    safe_course["due"] = _bool_value(safe_course["due"])
    safe_course["minutes_until_start"] = _non_negative_int(
        safe_course["minutes_until_start"]
    )
    safe_course["stop_after_minutes"] = _positive_duration(
        safe_course["stop_after_minutes"]
    )
    safe_course["enabled"] = _bool_value(safe_course["enabled"])
    safe_course["requires_confirmation"] = _bool_value(
        safe_course["requires_confirmation"]
    )
    if (
        safe_course["due"] is not True
        or safe_course["minutes_until_start"] != 0
        or safe_course["enabled"] is not True
        or safe_course["requires_confirmation"] is not True
    ):
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
    return safe_course


def _response_courses(
    value: object,
    confirmation_response: str,
) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
    courses = [
        _response_course_safe_summary(course, confirmation_response) for course in value
    ]
    _ensure_unique_sorted_courses(courses)
    courses.sort(
        key=lambda course: (
            str(course["course_id"]),
            int(course["selected_class_time_index"]),
        )
    )
    return courses


def _response_course_safe_summary(
    payload: object,
    confirmation_response: str,
) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
    safe_course = {key: payload[key] for key in _RESPONSE_COURSE_KEYS}
    safe_preflight_course = _preflight_course_safe_summary(
        {key: safe_course[key] for key in _PREFLIGHT_COURSE_KEYS}
    )
    course_response = _confirmation_response_token(safe_course["confirmation_response"])
    if course_response != confirmation_response:
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
    return {**safe_preflight_course, "confirmation_response": course_response}


def _validate_response_policy(
    *,
    status: str,
    confirmation_status: str,
    confirmation_response: str,
    due_count: int,
    ready_to_start: bool,
    confirmation_required: bool,
    confirmation_verified: bool,
    confirmed_start_count: int,
    blocked_execution_count: int,
    courses: object,
) -> None:
    if status == "confirmed":
        if confirmation_status != "required" or confirmation_response != "confirmed":
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
        if not ready_to_start or not confirmation_required or due_count <= 0:
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
        if not confirmation_verified or confirmed_start_count != due_count:
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
        if blocked_execution_count != 0:
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
    elif status == "declined":
        if confirmation_status != "required" or confirmation_response != "declined":
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
        if not ready_to_start or not confirmation_required or due_count <= 0:
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
        if confirmation_verified or confirmed_start_count != 0:
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
        if blocked_execution_count != due_count:
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
    elif status == "not_required":
        if confirmation_status != "not_required":
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
        if ready_to_start or confirmation_required or due_count != 0:
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
        if confirmation_verified or confirmed_start_count != 0:
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
        if blocked_execution_count != 0 or courses:
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
    elif status == "disabled":
        if confirmation_status != "disabled":
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
        if ready_to_start or confirmation_required or due_count != 0:
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
        if confirmation_verified or confirmed_start_count != 0:
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
        if blocked_execution_count != 0 or courses:
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)


def _ensure_unique_sorted_courses(courses: list[dict[str, object]]) -> None:
    seen: set[tuple[str, int]] = set()
    for course in courses:
        key = (
            str(course["course_id"]),
            int(course["selected_class_time_index"]),
        )
        if key in seen:
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
        seen.add(key)


def _safe_session_id(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
    if value != value.strip() or not value:
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
    if _has_control_character(value) or "/" in value or "\\" in value:
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
    if ":" in value or "://" in value or ".." in value:
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
    if _SESSION_ID_PATTERN.fullmatch(value) is None:
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
    reserved_candidate = value.split(".", maxsplit=1)[0].upper()
    if reserved_candidate in _WINDOWS_RESERVED_SESSION_NAMES:
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
    return value


def _safe_course_id(value: object) -> str:
    if not isinstance(value, str) or _COURSE_ID_PATTERN.fullmatch(value) is None:
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
    return value


def _source_kind(value: object) -> str:
    if not isinstance(value, str) or value not in _SOURCE_KINDS:
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
    return value


def _day_of_week(value: object) -> str:
    if not isinstance(value, str) or value not in _DAYS_OF_WEEK:
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
    return value


def _local_time(value: object) -> str:
    if not isinstance(value, str) or _LOCAL_TIME_PATTERN.fullmatch(value) is None:
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
    hour_text, minute_text = value.split(":")
    if int(hour_text) > 23 or int(minute_text) > 59:
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
    return value


def _preflight_status(value: object) -> str:
    if not isinstance(value, str) or value not in _PREFLIGHT_STATUSES:
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
    return value


def _response_status(value: object) -> str:
    if not isinstance(value, str) or value not in _RESPONSE_STATUSES:
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
    return value


def _confirmation_response_token(value: object) -> str:
    if not isinstance(value, str) or value not in _CONFIRMATION_RESPONSE_TOKENS:
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
    return value


def _bool_value(value: object) -> bool:
    if not isinstance(value, bool):
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
    return value


def _non_negative_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
    return value


def _positive_duration(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
    if value <= 0 or value > 24 * 60:
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR)
    return value


def _has_control_character(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)
