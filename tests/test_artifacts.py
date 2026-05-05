from __future__ import annotations

import json
from datetime import UTC, datetime

from async_scholar.artifacts import (
    safe_session_id,
    write_alert_log,
    write_events_jsonl,
    write_reviewer_markdown,
)
from async_scholar.schemas import LectureEvent, TranscriptSegment


def test_write_events_jsonl_writes_one_event_per_line(tmp_path) -> None:
    event = _event()

    events_path = write_events_jsonl([event], tmp_path)

    lines = events_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["event_id"] == "fixture:demo:event:0001:attendance_prompt"
    assert payload["session_id"] == "fixture:demo"
    assert payload["event_type"] == "attendance_prompt"
    assert payload["source_segment_ids"] == ["fixture:demo:segment:0001"]


def test_write_alert_log_is_concise_and_omits_transcript_text(tmp_path) -> None:
    event = _event()
    transcript_text = "Good morning. I am going to take attendance before we begin."

    alerts_path = write_alert_log(
        [event],
        tmp_path,
        created_at=datetime(2026, 5, 5, 0, 0, tzinfo=UTC),
    )

    log_text = alerts_path.read_text(encoding="utf-8")
    payload = json.loads(log_text)
    assert payload["alert_id"] == "fixture:demo:event:0001:attendance_prompt:alert"
    assert payload["event_id"] == event.event_id
    assert payload["event_type"] == "attendance_prompt"
    assert payload["message"] == "Attendance prompt detected."
    assert payload["requires_confirmation"] is True
    assert payload["status"] == "pending"
    assert transcript_text not in log_text


def test_write_reviewer_markdown_uses_only_detected_event_snippets(tmp_path) -> None:
    detected_segment = _segment(
        segment_id="fixture:demo:segment:0001",
        text="Good morning. I am going to take attendance before we begin.",
    )
    unrelated_segment = _segment(
        segment_id="fixture:demo:segment:0002",
        text="This unrelated sentence should not appear in the reviewer.",
    )

    reviewer_path = write_reviewer_markdown(
        [_event()],
        [detected_segment, unrelated_segment],
        tmp_path,
    )

    reviewer = reviewer_path.read_text(encoding="utf-8")
    assert "Attendance Prompt" in reviewer
    assert "instructor: Good morning. I am going to take attendance" in reviewer
    assert "This unrelated sentence should not appear" not in reviewer


def test_safe_session_id_replaces_path_unsafe_characters() -> None:
    assert (
        safe_session_id("fixture:attendance/roll call")
        == "fixture_attendance_roll_call"
    )


def _event() -> LectureEvent:
    return LectureEvent(
        event_id="fixture:demo:event:0001:attendance_prompt",
        session_id="fixture:demo",
        event_type="attendance_prompt",
        detected_at_seconds=0.0,
        source_segment_ids=("fixture:demo:segment:0001",),
        message="Attendance prompt detected.",
        confidence=0.95,
    )


def _segment(*, segment_id: str, text: str) -> TranscriptSegment:
    return TranscriptSegment(
        segment_id=segment_id,
        session_id="fixture:demo",
        start_seconds=0.0,
        end_seconds=2.0,
        text=text,
        speaker="instructor",
    )
