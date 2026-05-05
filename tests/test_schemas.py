from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from async_scholar.schemas import (
    Alert,
    LectureEvent,
    SessionMetadata,
    TranscriptSegment,
)

STARTED_AT = datetime(2026, 5, 5, 8, 30, tzinfo=UTC)


def test_transcript_segment_creation() -> None:
    segment = TranscriptSegment(
        segment_id="segment-001",
        session_id="session-001",
        start_seconds=12.5,
        end_seconds=15.0,
        text="Please answer the attendance poll.",
        speaker="Instructor",
    )

    assert segment.text == "Please answer the attendance poll."
    assert segment.speaker == "Instructor"


def test_transcript_segment_rejects_invalid_time_range() -> None:
    with pytest.raises(ValidationError):
        TranscriptSegment(
            segment_id="segment-001",
            session_id="session-001",
            start_seconds=15.0,
            end_seconds=12.5,
            text="This segment has impossible timing.",
        )


def test_lecture_event_creation() -> None:
    event = LectureEvent(
        event_id="event-001",
        session_id="session-001",
        event_type="attendance_prompt",
        detected_at_seconds=12.5,
        source_segment_ids=("segment-001",),
        message="Attendance prompt detected.",
        confidence=0.92,
    )

    assert event.source_segment_ids == ("segment-001",)
    assert event.confidence == 0.92


def test_lecture_event_rejects_missing_source_segments() -> None:
    with pytest.raises(ValidationError):
        LectureEvent(
            event_id="event-001",
            session_id="session-001",
            event_type="attendance_prompt",
            detected_at_seconds=12.5,
            source_segment_ids=(),
            message="Attendance prompt detected.",
        )


def test_alert_creation() -> None:
    alert = Alert(
        alert_id="alert-001",
        session_id="session-001",
        event_id="event-001",
        message="Attendance prompt needs your confirmation.",
        created_at=STARTED_AT + timedelta(minutes=5),
        status="sent",
    )

    assert alert.requires_confirmation is True
    assert alert.status == "sent"


def test_alert_rejects_unknown_status() -> None:
    with pytest.raises(ValidationError):
        Alert(
            alert_id="alert-001",
            session_id="session-001",
            event_id="event-001",
            message="Attendance prompt needs your confirmation.",
            created_at=STARTED_AT + timedelta(minutes=5),
            status="dismissed",
        )


def test_session_metadata_creation() -> None:
    session = SessionMetadata(
        session_id="session-001",
        course_id="course-001",
        course_title="Intro to Async Systems",
        started_at=STARTED_AT,
        ended_at=STARTED_AT + timedelta(minutes=75),
    )

    assert session.course_title == "Intro to Async Systems"
    assert session.ended_at == STARTED_AT + timedelta(minutes=75)


def test_session_metadata_rejects_end_before_start() -> None:
    with pytest.raises(ValidationError):
        SessionMetadata(
            session_id="session-001",
            course_id="course-001",
            course_title="Intro to Async Systems",
            started_at=STARTED_AT,
            ended_at=STARTED_AT - timedelta(minutes=1),
        )
