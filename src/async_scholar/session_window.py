"""Pure stored session-window plan helpers."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from async_scholar.schedule_config import ScheduleConfig
from async_scholar.scheduled_start import (
    ScheduledStartClock,
    build_scheduled_start_due_list_summary,
    build_scheduled_start_manual_result,
    build_scheduled_start_plan,
    scheduled_start_manual_result_safe_summary,
)

STORED_SESSION_WINDOW_PLAN_ERROR = "stored session window plan could not be built"

StoredSessionWindowPlanSummary = dict[str, object]


def build_stored_session_window_plan_summary(
    stored_courses: dict[str, object],
    clock: ScheduledStartClock,
    session_id: str,
    source_kind: str,
    *,
    enabled: bool = True,
) -> StoredSessionWindowPlanSummary:
    """Build due-only stored session window metadata without execution."""

    try:
        if not isinstance(stored_courses, dict):
            raise ValueError(STORED_SESSION_WINDOW_PLAN_ERROR)
        if type(clock) is not ScheduledStartClock:
            raise ValueError(STORED_SESSION_WINDOW_PLAN_ERROR)
        if not isinstance(enabled, bool):
            raise ValueError(STORED_SESSION_WINDOW_PLAN_ERROR)

        due_list = build_scheduled_start_due_list_summary(
            _due_list_inputs_from_window_inputs(stored_courses),
            clock,
            session_id,
            source_kind,
            enabled=enabled,
        )
        if not enabled:
            return due_list

        course_rows = _normalize_window_courses(stored_courses["courses"])
        window_courses = []
        for course in course_rows:
            class_times = course["class_times"]
            if not isinstance(class_times, list):
                raise ValueError(STORED_SESSION_WINDOW_PLAN_ERROR)
            for class_time in class_times:
                if not isinstance(class_time, dict):
                    raise ValueError(STORED_SESSION_WINDOW_PLAN_ERROR)
                preview = scheduled_start_manual_result_safe_summary(
                    build_scheduled_start_manual_result(
                        build_scheduled_start_plan(
                            ScheduleConfig(
                                course_id=course["course_id"],
                                class_times=[
                                    {
                                        "day_of_week": class_time[
                                            "scheduled_day_of_week"
                                        ],
                                        "local_start_time": class_time[
                                            "scheduled_local_start_time"
                                        ],
                                        "duration_minutes": class_time[
                                            "stop_after_minutes"
                                        ],
                                    }
                                ],
                            ),
                            selected_class_time_index=0,
                            source_kind=source_kind,
                        ),
                        clock,
                        session_id,
                    )
                )
                if preview["due"] is not True:
                    continue
                window_courses.append(
                    {
                        "course_id": preview["course_id"],
                        "selected_class_time_index": class_time[
                            "selected_class_time_index"
                        ],
                        "scheduled_day_of_week": preview["scheduled_day_of_week"],
                        "scheduled_local_start_time": preview[
                            "scheduled_local_start_time"
                        ],
                        "due": True,
                        "minutes_until_start": preview["minutes_until_start"],
                        "stop_after_minutes": class_time["stop_after_minutes"],
                        "enabled": True,
                    }
                )
        window_courses.sort(
            key=lambda course: (
                str(course["course_id"]),
                int(course["selected_class_time_index"]),
            )
        )
        return {
            **due_list,
            "status": "due" if window_courses else "waiting",
            "due_count": len(window_courses),
            "courses": window_courses,
        }
    except (
        KeyError,
        IndexError,
        TypeError,
        ValidationError,
        ValueError,
    ):
        raise ValueError(STORED_SESSION_WINDOW_PLAN_ERROR) from None


def _due_list_inputs_from_window_inputs(
    stored_courses: dict[str, object],
) -> dict[str, object]:
    course_count = _normalize_course_count(stored_courses["course_count"])
    courses = _normalize_window_courses(stored_courses["courses"])
    if len(courses) != course_count:
        raise ValueError(STORED_SESSION_WINDOW_PLAN_ERROR)
    return {
        "course_count": course_count,
        "courses": [
            {
                "course_id": course["course_id"],
                "class_times": [
                    {
                        "selected_class_time_index": class_time[
                            "selected_class_time_index"
                        ],
                        "scheduled_day_of_week": class_time["scheduled_day_of_week"],
                        "scheduled_local_start_time": class_time[
                            "scheduled_local_start_time"
                        ],
                    }
                    for class_time in course["class_times"]
                ],
            }
            for course in courses
        ],
    }


def _normalize_course_count(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(STORED_SESSION_WINDOW_PLAN_ERROR)
    return value


def _normalize_window_courses(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(STORED_SESSION_WINDOW_PLAN_ERROR)
    courses: list[dict[str, Any]] = []
    for course in value:
        if not isinstance(course, dict):
            raise ValueError(STORED_SESSION_WINDOW_PLAN_ERROR)
        class_times = course["class_times"]
        if not isinstance(class_times, list) or not class_times:
            raise ValueError(STORED_SESSION_WINDOW_PLAN_ERROR)
        normalized_class_times = []
        for class_time in class_times:
            if not isinstance(class_time, dict):
                raise ValueError(STORED_SESSION_WINDOW_PLAN_ERROR)
            normalized_class_times.append(
                {
                    **class_time,
                    "stop_after_minutes": _normalize_stop_after_minutes(
                        class_time["stop_after_minutes"]
                    ),
                }
            )
        schedule_config = ScheduleConfig(
            course_id=course["course_id"],
            class_times=[
                {
                    "day_of_week": class_time["scheduled_day_of_week"],
                    "local_start_time": class_time["scheduled_local_start_time"],
                    "duration_minutes": class_time["stop_after_minutes"],
                }
                for class_time in normalized_class_times
            ],
        )
        for class_time in normalized_class_times:
            class_time["selected_class_time_index"] = _normalize_class_time_index(
                class_time["selected_class_time_index"]
            )
        courses.append(
            {
                "course_id": schedule_config.course_id,
                "class_times": normalized_class_times,
            }
        )
    return courses


def _normalize_class_time_index(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(STORED_SESSION_WINDOW_PLAN_ERROR)
    return value


def _normalize_stop_after_minutes(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(STORED_SESSION_WINDOW_PLAN_ERROR)
    return value
