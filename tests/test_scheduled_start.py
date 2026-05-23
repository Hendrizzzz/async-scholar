import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from async_scholar import scheduled_start
from async_scholar.schedule_config import ScheduleConfig
from async_scholar.scheduled_start import (
    SCHEDULED_START_MANUAL_RESULT_ERROR,
    SCHEDULED_START_NEXT_PREVIEW_ERROR,
    ScheduledStartClock,
    ScheduledStartDueDecision,
    ScheduledStartManualResult,
    ScheduledStartPlan,
    build_next_scheduled_start_preview_summary,
    build_scheduled_start_due_decision,
    build_scheduled_start_manual_result,
    build_scheduled_start_plan,
    scheduled_start_manual_result_safe_summary,
    scheduled_start_manual_result_to_json_ready,
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


def test_scheduled_start_clock_normalizes_explicit_clock_input() -> None:
    clock = ScheduledStartClock(day_of_week=" MONDAY ", local_time="\t09:00\n")

    assert clock.day_of_week == "monday"
    assert clock.local_time == "09:00"
    assert clock.to_json_ready() == {
        "day_of_week": "monday",
        "local_time": "09:00",
    }
    assert clock.safe_summary() == clock.to_json_ready()
    assert clock.to_safe_export() == clock.to_json_ready()


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("day_of_week", ""),
        ("day_of_week", "mon"),
        ("day_of_week", "funday"),
        ("day_of_week", 1),
        ("local_time", ""),
        ("local_time", "9:00"),
        ("local_time", "24:00"),
        ("local_time", "12:60"),
        ("local_time", "12:00:00"),
        ("local_time", 900),
    ],
)
def test_scheduled_start_clock_rejects_invalid_clock_values(
    field_name: str,
    value: object,
) -> None:
    values = {"day_of_week": "monday", "local_time": "09:00"}
    values[field_name] = value

    with pytest.raises(ValidationError):
        ScheduledStartClock(**values)


def test_scheduled_start_clock_rejects_extra_fields_and_is_immutable() -> None:
    with pytest.raises(ValidationError):
        ScheduledStartClock(
            day_of_week="monday",
            local_time="09:00",
            system_time="2026-05-17T09:00:00",
        )

    clock = ScheduledStartClock(day_of_week="monday", local_time="09:00")
    with pytest.raises((TypeError, ValidationError)):
        clock.local_time = "09:01"


def test_due_decision_marks_exact_enabled_clock_due() -> None:
    plan = build_scheduled_start_plan(
        _schedule_config(),
        selected_class_time_index=0,
        source_kind="file",
    )
    clock = ScheduledStartClock(day_of_week="monday", local_time="09:00")

    decision = build_scheduled_start_due_decision(plan, clock)

    assert decision == ScheduledStartDueDecision(
        status="due",
        course_id="cs_101",
        source_kind="file",
        enabled=True,
        clock_day_of_week="monday",
        clock_local_time="09:00",
        scheduled_day_of_week="monday",
        scheduled_local_start_time="09:00",
        due=True,
        minutes_until_start=0,
        next_day_of_week="monday",
        next_local_start_time="09:00",
    )


def test_due_decision_reports_same_day_future_start() -> None:
    plan = build_scheduled_start_plan(
        _schedule_config(),
        selected_class_time_index=0,
        source_kind="file",
    )
    clock = ScheduledStartClock(day_of_week="monday", local_time="08:30")

    decision = build_scheduled_start_due_decision(plan, clock)

    assert decision.status == "waiting"
    assert decision.due is False
    assert decision.minutes_until_start == 30
    assert decision.next_day_of_week == "monday"
    assert decision.next_local_start_time == "09:00"


def test_due_decision_wraps_after_scheduled_minute_passes() -> None:
    plan = build_scheduled_start_plan(
        _schedule_config(),
        selected_class_time_index=0,
        source_kind="file",
    )
    clock = ScheduledStartClock(day_of_week="monday", local_time="09:01")

    decision = build_scheduled_start_due_decision(plan, clock)

    assert decision.status == "waiting"
    assert decision.due is False
    assert decision.minutes_until_start == (7 * 24 * 60) - 1
    assert decision.next_day_of_week == "monday"
    assert decision.next_local_start_time == "09:00"


def test_due_decision_wraps_from_late_week_to_next_class() -> None:
    plan = build_scheduled_start_plan(
        _schedule_config(),
        selected_class_time_index=0,
        source_kind="file",
    )
    clock = ScheduledStartClock(day_of_week="sunday", local_time="23:59")

    decision = build_scheduled_start_due_decision(plan, clock)

    assert decision.status == "waiting"
    assert decision.due is False
    assert decision.minutes_until_start == 9 * 60 + 1
    assert decision.next_day_of_week == "monday"
    assert decision.next_local_start_time == "09:00"


def test_due_decision_disables_due_and_next_timing_for_disabled_plans() -> None:
    plan = build_scheduled_start_plan(
        _schedule_config(),
        selected_class_time_index=0,
        source_kind="file",
        enabled=False,
    )
    clock = ScheduledStartClock(day_of_week="monday", local_time="09:00")

    decision = build_scheduled_start_due_decision(plan, clock)

    assert decision.status == "disabled"
    assert decision.enabled is False
    assert decision.due is False
    assert decision.minutes_until_start is None
    assert decision.next_day_of_week is None
    assert decision.next_local_start_time is None


def test_due_decision_rejects_invalid_input_types() -> None:
    plan = build_scheduled_start_plan(
        _schedule_config(),
        selected_class_time_index=0,
        source_kind="file",
    )
    clock = ScheduledStartClock(day_of_week="monday", local_time="09:00")

    with pytest.raises(ValueError):
        build_scheduled_start_due_decision({"course_id": "cs101"}, clock)

    with pytest.raises(ValueError):
        build_scheduled_start_due_decision(plan, {"day_of_week": "monday"})


def test_due_decision_rejects_subclass_inputs() -> None:
    class ScheduledStartPlanSubclass(ScheduledStartPlan):
        pass

    class ScheduledStartClockSubclass(ScheduledStartClock):
        pass

    plan = ScheduledStartPlanSubclass(
        course_id="cs101",
        day_of_week="monday",
        local_start_time="09:00",
        duration_minutes=60,
        source_kind="file",
    )
    clock = ScheduledStartClock(day_of_week="monday", local_time="09:00")

    with pytest.raises(ValueError):
        build_scheduled_start_due_decision(plan, clock)

    exact_plan = ScheduledStartPlan(
        course_id="cs101",
        day_of_week="monday",
        local_start_time="09:00",
        duration_minutes=60,
        source_kind="file",
    )
    subclass_clock = ScheduledStartClockSubclass(
        day_of_week="monday",
        local_time="09:00",
    )

    with pytest.raises(ValueError):
        build_scheduled_start_due_decision(exact_plan, subclass_clock)


def test_due_decision_revalidates_constructed_inputs_without_raw_leakage() -> None:
    if not hasattr(ScheduledStartClock, "model_construct"):
        pytest.skip("Pydantic v2 model_construct is not available")

    plan = build_scheduled_start_plan(
        _schedule_config(),
        selected_class_time_index=0,
        source_kind="file",
    )
    unsafe_clock = ScheduledStartClock.model_construct(
        day_of_week="monday",
        local_time="C:/Users/student/secrets/.env",
    )

    with pytest.raises(ValueError) as exc_info:
        build_scheduled_start_due_decision(plan, unsafe_clock)

    error_text = str(exc_info.value)
    assert error_text == "scheduled start preflight input failed validation"
    for forbidden_text in ["C:", "Users", "secrets", ".env"]:
        assert forbidden_text not in error_text


def test_due_decision_json_ready_and_safe_summary_contents() -> None:
    plan = build_scheduled_start_plan(
        _schedule_config(),
        selected_class_time_index=0,
        source_kind="file",
    )
    clock = ScheduledStartClock(day_of_week="monday", local_time="08:30")

    decision = build_scheduled_start_due_decision(plan, clock)

    expected = {
        "decision_kind": "scheduled_start_due_decision",
        "status": "waiting",
        "course_id": "cs_101",
        "source_kind": "file",
        "enabled": True,
        "clock_day_of_week": "monday",
        "clock_local_time": "08:30",
        "scheduled_day_of_week": "monday",
        "scheduled_local_start_time": "09:00",
        "due": False,
        "minutes_until_start": 30,
        "next_day_of_week": "monday",
        "next_local_start_time": "09:00",
    }

    assert decision.to_json_ready() == expected
    assert decision.to_safe_summary() == expected
    assert decision.safe_summary() == expected
    assert decision.to_safe_export() == expected
    assert json.loads(json.dumps(decision.to_json_ready(), sort_keys=True)) == expected


def test_due_decision_summary_exposes_no_private_or_execution_data() -> None:
    plan = build_scheduled_start_plan(
        _schedule_config(),
        selected_class_time_index=0,
        source_kind="file",
    )
    clock = ScheduledStartClock(day_of_week="monday", local_time="08:30")

    decision = build_scheduled_start_due_decision(plan, clock)

    summary_text = json.dumps(decision.to_json_ready(), sort_keys=True)
    for forbidden_text in [
        "meeting_label",
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
        "notification",
        "payload",
        "timer",
        "worker",
        "runner",
        "exception",
        "raw",
    ]:
        assert forbidden_text not in summary_text


def test_due_decision_is_immutable() -> None:
    plan = build_scheduled_start_plan(
        _schedule_config(),
        selected_class_time_index=0,
        source_kind="file",
    )
    clock = ScheduledStartClock(day_of_week="monday", local_time="09:00")
    decision = build_scheduled_start_due_decision(plan, clock)

    with pytest.raises((TypeError, ValidationError)):
        decision.due = False


def test_manual_result_reports_due_metadata_without_private_plan_text() -> None:
    plan = ScheduledStartPlan(
        course_id="CS_101",
        day_of_week="Monday",
        local_start_time="09:00",
        duration_minutes=75,
        timezone_name="Asia/Manila token secret auth profile",
        meeting_label="Private lecture token secret auth profile",
        source_kind="file",
    )
    clock = ScheduledStartClock(day_of_week="monday", local_time="09:00")

    result = build_scheduled_start_manual_result(plan, clock, "session-001")
    payload = scheduled_start_manual_result_to_json_ready(result)

    expected = {
        "result_kind": "scheduled_start_manual_result",
        "status": "due",
        "session_id": "session-001",
        "course_id": "cs_101",
        "source_kind": "file",
        "enabled": True,
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "scheduled_day_of_week": "monday",
        "scheduled_local_start_time": "09:00",
        "due": True,
        "minutes_until_start": 0,
        "next_day_of_week": "monday",
        "next_local_start_time": "09:00",
    }
    assert result == ScheduledStartManualResult(**expected)
    assert payload == expected
    assert result.to_json_ready() == expected
    assert result.safe_summary() == expected
    assert result.to_safe_export() == expected
    assert json.loads(json.dumps(payload, sort_keys=True)) == expected

    output_text = json.dumps(payload, sort_keys=True).lower()
    for forbidden_text in (
        "meeting_label",
        "timezone_name",
        "private lecture",
        "asia/manila",
        "token",
        "secret",
        "auth",
        "profile",
        "started",
        "executed",
        "notified",
        "opened",
        "recording",
        "artifact",
    ):
        assert forbidden_text not in output_text


def test_manual_result_reports_waiting_metadata() -> None:
    plan = build_scheduled_start_plan(
        _schedule_config(),
        selected_class_time_index=0,
        source_kind="file",
    )
    clock = ScheduledStartClock(day_of_week="monday", local_time="08:30")

    payload = build_scheduled_start_manual_result(
        plan,
        clock,
        "session-001",
    ).to_json_ready()

    assert payload["status"] == "waiting"
    assert payload["due"] is False
    assert payload["minutes_until_start"] == 30
    assert payload["next_day_of_week"] == "monday"
    assert payload["next_local_start_time"] == "09:00"


def test_manual_result_reports_disabled_metadata() -> None:
    plan = build_scheduled_start_plan(
        _schedule_config(),
        selected_class_time_index=0,
        source_kind="file",
        enabled=False,
    )
    clock = ScheduledStartClock(day_of_week="monday", local_time="09:00")

    payload = build_scheduled_start_manual_result(
        plan,
        clock,
        "session-001",
    ).to_json_ready()

    assert payload["status"] == "disabled"
    assert payload["enabled"] is False
    assert payload["due"] is False
    assert payload["minutes_until_start"] is None
    assert payload["next_day_of_week"] is None
    assert payload["next_local_start_time"] is None


@pytest.mark.parametrize(
    "session_id",
    [
        "",
        "   ",
        ".hidden",
        "../session",
        "session/one",
        "session\\one",
        "C:session",
        "\\\\server\\share",
        "https://example.test/session",
        "session\none",
        "session one",
        "CON",
        "con.txt",
        "LPT1.session",
    ],
)
def test_manual_result_rejects_unsafe_session_ids(session_id: object) -> None:
    plan = build_scheduled_start_plan(
        _schedule_config(),
        selected_class_time_index=0,
        source_kind="file",
    )
    clock = ScheduledStartClock(day_of_week="monday", local_time="09:00")

    with pytest.raises(ValueError) as exc_info:
        build_scheduled_start_manual_result(plan, clock, session_id)

    assert str(exc_info.value) == SCHEDULED_START_MANUAL_RESULT_ERROR


def test_manual_result_rejects_invalid_input_types_with_fixed_error() -> None:
    plan = build_scheduled_start_plan(
        _schedule_config(),
        selected_class_time_index=0,
        source_kind="file",
    )
    clock = ScheduledStartClock(day_of_week="monday", local_time="09:00")

    for args in (
        ({"course_id": "cs101"}, clock, "session-001"),
        (plan, {"day_of_week": "monday"}, "session-001"),
    ):
        with pytest.raises(ValueError) as exc_info:
            build_scheduled_start_manual_result(*args)

        assert str(exc_info.value) == SCHEDULED_START_MANUAL_RESULT_ERROR


def test_manual_result_rejects_subclass_inputs_with_fixed_error() -> None:
    class ScheduledStartPlanSubclass(ScheduledStartPlan):
        pass

    class ScheduledStartClockSubclass(ScheduledStartClock):
        pass

    plan = ScheduledStartPlanSubclass(
        course_id="cs101",
        day_of_week="monday",
        local_start_time="09:00",
        duration_minutes=60,
        source_kind="file",
    )
    clock = ScheduledStartClock(day_of_week="monday", local_time="09:00")

    with pytest.raises(ValueError) as exc_info:
        build_scheduled_start_manual_result(plan, clock, "session-001")

    assert str(exc_info.value) == SCHEDULED_START_MANUAL_RESULT_ERROR

    exact_plan = ScheduledStartPlan(
        course_id="cs101",
        day_of_week="monday",
        local_start_time="09:00",
        duration_minutes=60,
        source_kind="file",
    )
    subclass_clock = ScheduledStartClockSubclass(
        day_of_week="monday",
        local_time="09:00",
    )

    with pytest.raises(ValueError) as exc_info:
        build_scheduled_start_manual_result(exact_plan, subclass_clock, "session-001")

    assert str(exc_info.value) == SCHEDULED_START_MANUAL_RESULT_ERROR


def test_manual_result_revalidates_constructed_inputs_without_raw_leakage() -> None:
    if not hasattr(ScheduledStartClock, "model_construct"):
        pytest.skip("Pydantic v2 model_construct is not available")

    plan = build_scheduled_start_plan(
        _schedule_config(),
        selected_class_time_index=0,
        source_kind="file",
    )
    unsafe_clock = ScheduledStartClock.model_construct(
        day_of_week="monday",
        local_time="C:/Users/student/secrets/.env",
    )

    with pytest.raises(ValueError) as exc_info:
        build_scheduled_start_manual_result(plan, unsafe_clock, "session-001")

    error_text = str(exc_info.value)
    assert error_text == SCHEDULED_START_MANUAL_RESULT_ERROR
    for forbidden_text in ("C:", "Users", "student", "secrets", ".env"):
        assert forbidden_text not in error_text


def test_manual_result_helpers_revalidate_constructed_result_without_leakage() -> None:
    if not hasattr(ScheduledStartManualResult, "model_construct"):
        pytest.skip("Pydantic v2 model_construct is not available")

    unsafe_result = ScheduledStartManualResult.model_construct(
        result_kind="scheduled_start_manual_result",
        status="due",
        session_id="C:/Users/student/session-token-secret-auth-profile",
        course_id="cs101",
        source_kind="file",
        enabled=True,
        clock_day_of_week="monday",
        clock_local_time="09:00",
        scheduled_day_of_week="monday",
        scheduled_local_start_time="09:00",
        due=True,
        minutes_until_start=0,
        next_day_of_week="monday",
        next_local_start_time="09:00",
    )

    for helper in (
        unsafe_result.to_json_ready,
        unsafe_result.safe_summary,
        lambda: scheduled_start_manual_result_to_json_ready(unsafe_result),
        lambda: scheduled_start_manual_result_safe_summary(unsafe_result),
    ):
        with pytest.raises(ValueError) as exc_info:
            helper()

        error_text = str(exc_info.value)
        assert error_text == SCHEDULED_START_MANUAL_RESULT_ERROR
        for forbidden_text in ("C:", "Users", "student", "token", "secret", "auth"):
            assert forbidden_text not in error_text


def test_manual_result_rejects_extra_fields_and_is_immutable() -> None:
    result = build_scheduled_start_manual_result(
        build_scheduled_start_plan(
            _schedule_config(),
            selected_class_time_index=0,
            source_kind="file",
        ),
        ScheduledStartClock(day_of_week="monday", local_time="09:00"),
        "session-001",
    )

    with pytest.raises(ValidationError):
        ScheduledStartManualResult(
            **result.to_json_ready(),
            started=True,
        )
    with pytest.raises((TypeError, ValidationError)):
        result.due = False


def test_next_preview_selects_exact_due_class_time() -> None:
    payload = build_next_scheduled_start_preview_summary(
        _schedule_config(),
        ScheduledStartClock(day_of_week="thursday", local_time="18:45"),
        "session-001",
        "mic",
    )

    assert payload == {
        "status": "due",
        "session_id": "session-001",
        "course_id": "cs_101",
        "source_kind": "mic",
        "clock_day_of_week": "thursday",
        "clock_local_time": "18:45",
        "selected_class_time_index": 1,
        "scheduled_day_of_week": "thursday",
        "scheduled_local_start_time": "18:45",
        "due": True,
        "minutes_until_start": 0,
        "next_day_of_week": "thursday",
        "next_local_start_time": "18:45",
    }


def test_next_preview_selects_nearest_same_day_future_class_time() -> None:
    payload = build_next_scheduled_start_preview_summary(
        _schedule_config(),
        ScheduledStartClock(day_of_week="monday", local_time="08:30"),
        "session-001",
        "file",
    )

    assert payload["status"] == "waiting"
    assert payload["selected_class_time_index"] == 0
    assert payload["minutes_until_start"] == 30
    assert payload["scheduled_day_of_week"] == "monday"
    assert payload["scheduled_local_start_time"] == "09:00"


def test_next_preview_wraps_to_next_week_class_time() -> None:
    payload = build_next_scheduled_start_preview_summary(
        _schedule_config(),
        ScheduledStartClock(day_of_week="sunday", local_time="23:59"),
        "session-001",
        "file",
    )

    assert payload["selected_class_time_index"] == 0
    assert payload["minutes_until_start"] == 541
    assert payload["next_day_of_week"] == "monday"
    assert payload["next_local_start_time"] == "09:00"


def test_next_preview_ties_use_lower_class_time_index() -> None:
    schedule_config = ScheduleConfig(
        course_id="cs101",
        class_times=[
            {
                "day_of_week": "monday",
                "local_start_time": "09:00",
                "duration_minutes": 60,
            },
            {
                "day_of_week": "monday",
                "local_start_time": "09:00",
                "duration_minutes": 90,
            },
        ],
    )

    payload = build_next_scheduled_start_preview_summary(
        schedule_config,
        ScheduledStartClock(day_of_week="monday", local_time="08:00"),
        "session-001",
        "file",
    )

    assert payload["selected_class_time_index"] == 0
    assert payload["minutes_until_start"] == 60


def test_next_preview_disabled_does_not_select_class_time() -> None:
    payload = build_next_scheduled_start_preview_summary(
        _schedule_config(),
        ScheduledStartClock(day_of_week="monday", local_time="09:00"),
        "session-001",
        "file",
        enabled=False,
    )

    assert payload == {
        "status": "disabled",
        "session_id": "session-001",
        "course_id": "cs_101",
        "source_kind": "file",
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "selected_class_time_index": None,
        "scheduled_day_of_week": None,
        "scheduled_local_start_time": None,
        "due": False,
        "minutes_until_start": None,
        "next_day_of_week": None,
        "next_local_start_time": None,
    }


def test_next_preview_summary_exposes_no_private_or_execution_data() -> None:
    payload = build_next_scheduled_start_preview_summary(
        _schedule_config(),
        ScheduledStartClock(day_of_week="monday", local_time="08:30"),
        "session-001",
        "file",
    )
    summary_text = json.dumps(payload, sort_keys=True)

    for forbidden_text in [
        "result_kind",
        "enabled",
        "timezone",
        "Asia/Manila",
        "Lecture",
        "duration",
        "meeting",
        "path",
        "browser",
        "auth",
        "cookie",
        "transcript",
        "audio",
    ]:
        assert forbidden_text not in summary_text


def test_next_preview_rejects_invalid_inputs_with_fixed_error() -> None:
    schedule_config = _schedule_config()
    clock = ScheduledStartClock(day_of_week="monday", local_time="09:00")

    for args in (
        ({"course_id": "cs101"}, clock, "session-001", "file"),
        (schedule_config, {"day_of_week": "monday"}, "session-001", "file"),
        (schedule_config, clock, "C:/Users/student/token-secret", "file"),
        (schedule_config, clock, "session-001", "browser"),
    ):
        with pytest.raises(ValueError) as exc_info:
            build_next_scheduled_start_preview_summary(*args)

        error_text = str(exc_info.value)
        assert error_text == SCHEDULED_START_NEXT_PREVIEW_ERROR
        for forbidden_text in ("C:", "Users", "student", "token", "secret"):
            assert forbidden_text not in error_text


def test_scheduled_start_module_has_no_execution_or_private_behavior() -> None:
    source = Path(scheduled_start.__file__).read_text(encoding="utf-8")

    forbidden_tokens = [
        "sqlite",
        "jsonl",
        "argparse",
        "sys.argv",
        "logging",
        "print(",
        "os.environ",
        ".env",
        "path",
        "open(",
        "read_text",
        "read_bytes",
        "write_text",
        "write_bytes",
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
        "multiprocessing",
        "multiprocessing",
        "zoneinfo",
        "datetime",
        "timedelta",
        "sleep(",
        "timer",
        "runner",
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
        "notification",
        "notifier",
        "telegram",
        "desktop_notifier",
        "archive_export",
        "archive_delete",
        "execute_archive_export",
        "unlink",
        "remove",
        "rmtree",
        "recording_path",
        "transcript_path",
        "archive_path",
        "artifact_path",
        "sqlite3",
        "socket",
        "urllib",
    ]

    normalized_source = source.lower()
    for forbidden_token in forbidden_tokens:
        assert forbidden_token not in normalized_source
