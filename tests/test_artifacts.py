from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import cast

import async_scholar.artifacts as artifacts
from async_scholar.alert_dispatch import AlertDispatchResult
from async_scholar.artifacts import (
    safe_session_id,
    write_alert_log,
    write_events_jsonl,
    write_reviewer_markdown,
    write_transcript_artifacts,
    write_transcript_jsonl,
    write_transcript_markdown,
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
    assert payload["alert_id"] == "alert-log-alert-0001"
    assert payload["event_id"] == "alert-log-event-0001"
    assert payload["session_id"] == "alert-log-session"
    assert payload["event_type"] == "attendance_prompt"
    assert payload["severity"] == "urgent"
    assert payload["dispatch_results"] == [
        {
            "provider": "file",
            "severity": "urgent",
            "status": "sent",
            "requires_confirmation": True,
        }
    ]
    assert set(payload["dispatch_results"][0]) == {
        "provider",
        "severity",
        "status",
        "requires_confirmation",
    }
    assert payload["retry_log_decisions"] == []
    assert payload["message"] == "Attendance prompt detected."
    assert payload["requires_confirmation"] is True
    assert payload["status"] == "pending"
    assert "source_segment_ids" not in payload
    assert transcript_text not in log_text


def test_write_alert_log_sanitizes_malformed_event_payload(tmp_path) -> None:
    event = LectureEvent(
        event_id=(
            "raw-event-id BOT_TOKEN=event-token chat_id=12345 "
            "https://api.telegram.org/bot-event-token/sendMessage"
        ),
        session_id=(
            "raw-session-id C:\\Users\\student\\.env browser-profile auth-state "
            "C:\\models\\private-model"
        ),
        event_type=(
            "raw_unknown_event transcript text C:\\Users\\student\\lecture.wav "
            "https://api.telegram.org/bot-token/sendMessage stdout stderr "
            "RuntimeError exception .env browser auth model-cache "
            "arbitrary-private-text"
        ),
        detected_at_seconds=99.0,
        source_segment_ids=(
            "raw-source-id C:\\Users\\student\\audio.mp3 browser-cookie",
        ),
        message=(
            "raw event.message transcript text says mark me present; "
            "BOT_TOKEN=message-token; CHAT_ID=12345; "
            "request URL https://api.telegram.org/bot-message-token/sendMessage; "
            "stdout dump; stderr dump; exception Traceback; .env; "
            "browser auth data; model path C:\\models\\private-model; "
            "raw audio path C:\\Users\\student\\lecture.wav; arbitrary unknown "
            "event text"
        ),
    )

    alerts_path = write_alert_log(
        [event],
        tmp_path,
        created_at=datetime(2026, 5, 5, 0, 0, tzinfo=UTC),
    )

    log_text = alerts_path.read_text(encoding="utf-8")
    payload = json.loads(log_text)
    assert payload["alert_id"] == "alert-log-alert-0001"
    assert payload["event_id"] == "alert-log-event-0001"
    assert payload["session_id"] == "alert-log-session"
    assert payload["event_type"] == "lecture_event"
    assert payload["message"] == "Lecture event detected."
    assert payload["severity"] == "normal"
    assert payload["dispatch_results"] == [
        {
            "provider": "file",
            "severity": "normal",
            "status": "sent",
            "requires_confirmation": True,
        }
    ]
    assert payload["retry_log_decisions"] == []
    assert payload["requires_confirmation"] is True
    assert payload["status"] == "pending"
    assert "source_segment_ids" not in payload

    for leaked_string in [
        "raw event.message",
        "mark me present",
        "raw_unknown_event",
        "raw-event-id",
        "raw-session-id",
        "raw-source-id",
        "C:\\Users\\student",
        "lecture.wav",
        "audio.mp3",
        "BOT_TOKEN",
        "event-token",
        "message-token",
        "CHAT_ID",
        "chat_id",
        "12345",
        "api.telegram.org",
        "sendMessage",
        "request URL",
        "stdout",
        "stderr",
        "RuntimeError",
        "Traceback",
        "exception",
        ".env",
        "browser",
        "auth",
        "private-model",
        "model-cache",
        "arbitrary-private-text",
        "arbitrary unknown event text",
        "transcript text",
    ]:
        assert leaked_string not in log_text


def test_write_alert_log_dispatch_result_omits_private_event_content(tmp_path) -> None:
    event = LectureEvent(
        event_id="event-secret-token",
        session_id="session-secret",
        event_type=(
            "BOT_TOKEN=secret-token C:\\Users\\student\\lecture.wav .env browser_cookie"
        ),
        detected_at_seconds=99.0,
        source_segment_ids=("segment-secret",),
        message="Lecture event detected.",
    )

    alerts_path = write_alert_log(
        [event],
        tmp_path,
        created_at=datetime(2026, 5, 5, 0, 0, tzinfo=UTC),
    )

    payload = json.loads(alerts_path.read_text(encoding="utf-8"))
    dispatch_results = payload["dispatch_results"]
    serialized_results = json.dumps(dispatch_results)
    assert dispatch_results == [
        {
            "provider": "file",
            "severity": "normal",
            "status": "sent",
            "requires_confirmation": True,
        }
    ]
    assert "source_segment_ids" not in payload
    assert "secret-token" not in serialized_results
    assert "C:\\Users\\student\\lecture.wav" not in serialized_results
    assert "lecture.wav" not in serialized_results
    assert ".env" not in serialized_results
    assert "browser_cookie" not in serialized_results
    assert "event-secret-token" not in serialized_results
    assert "session-secret" not in serialized_results
    assert "segment-secret" not in serialized_results


def test_write_alert_log_records_sanitized_retry_log_decisions(
    tmp_path,
    monkeypatch,
) -> None:
    event = LectureEvent(
        event_id="event-secret-token",
        session_id="session-secret",
        event_type="attendance_prompt",
        detected_at_seconds=99.0,
        source_segment_ids=("segment-secret",),
        message="Lecture event detected.",
    )
    dispatch_results = cast(
        list[AlertDispatchResult],
        [
            {
                "provider": "telegram",
                "severity": "urgent",
                "status": "failed",
                "requires_confirmation": True,
                "error_kind": "timeout",
            },
            {
                "provider": "desktop",
                "severity": "urgent",
                "status": "skipped",
                "requires_confirmation": True,
                "error_kind": "missing_dispatcher",
            },
            {
                "provider": "file",
                "severity": "urgent",
                "status": "sent",
                "requires_confirmation": True,
            },
        ],
    )

    def fake_dispatch_alert(
        event_arg: LectureEvent,
        provider_names: object,
        dispatchers: object,
    ) -> list[AlertDispatchResult]:
        assert event_arg == event
        assert provider_names == ("file",)
        assert "file" in dispatchers
        return dispatch_results

    monkeypatch.setattr(artifacts, "dispatch_alert", fake_dispatch_alert)

    alerts_path = write_alert_log(
        [event],
        tmp_path,
        created_at=datetime(2026, 5, 5, 0, 0, tzinfo=UTC),
    )

    payload = json.loads(alerts_path.read_text(encoding="utf-8"))
    assert payload["retry_log_decisions"] == [
        {
            "provider": "telegram",
            "severity": "urgent",
            "status": "failed",
            "requires_confirmation": True,
            "error_kind": "timeout",
            "retry_action": "retry",
            "max_attempts": 3,
        },
        {
            "provider": "desktop",
            "severity": "urgent",
            "status": "skipped",
            "requires_confirmation": True,
            "error_kind": "missing_dispatcher",
            "retry_action": "manual_check",
            "max_attempts": 0,
        },
    ]
    assert [set(decision) for decision in payload["retry_log_decisions"]] == [
        {
            "provider",
            "severity",
            "status",
            "requires_confirmation",
            "error_kind",
            "retry_action",
            "max_attempts",
        },
        {
            "provider",
            "severity",
            "status",
            "requires_confirmation",
            "error_kind",
            "retry_action",
            "max_attempts",
        },
    ]

    serialized_retry_decisions = json.dumps(payload["retry_log_decisions"])
    for leaked_string in [
        "raw transcript",
        "segment-secret",
        "event-secret",
        "session-secret",
        ".env",
        "lecture.wav",
        "secret-token",
        "12345",
        "sendMessage",
        "stdout",
        "stderr",
        "raw exception",
        "auth data",
        "private-model",
        "Lecture event detected",
    ]:
        assert leaked_string not in serialized_retry_decisions


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


def test_write_transcript_jsonl_writes_one_segment_per_line(tmp_path) -> None:
    segments = [
        _segment(
            segment_id="fixture:demo:segment:0001",
            text="Good morning. We will start with the agenda.",
        ),
        _segment(
            segment_id="fixture:demo:segment:0002",
            text="Please answer when I call your name.",
        ),
    ]

    transcript_path = write_transcript_jsonl(segments, tmp_path)

    lines = transcript_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    first_payload = json.loads(lines[0])
    assert first_payload["segment_id"] == "fixture:demo:segment:0001"
    assert first_payload["session_id"] == "fixture:demo"
    assert first_payload["start_seconds"] == 0.0
    assert first_payload["end_seconds"] == 2.0
    assert first_payload["speaker"] == "instructor"
    assert first_payload["text"] == "Good morning. We will start with the agenda."


def test_write_transcript_markdown_is_readable_and_ordered(tmp_path) -> None:
    first_segment = _segment(
        segment_id="fixture:demo:segment:0001",
        text="First sentence.",
    )
    second_segment = TranscriptSegment(
        segment_id="fixture:demo:segment:0002",
        session_id="fixture:demo",
        start_seconds=2.0,
        end_seconds=4.5,
        text="Second sentence without a speaker.",
    )

    transcript_path = write_transcript_markdown(
        session_id="fixture:demo",
        segments=[first_segment, second_segment],
        output_dir=tmp_path,
    )

    transcript = transcript_path.read_text(encoding="utf-8")
    assert "Session: `fixture:demo`" in transcript
    assert "Segments: 2" in transcript
    assert "## 0s - 2s" in transcript
    assert "**instructor:** First sentence." in transcript
    assert "## 2s - 4.5s" in transcript
    assert "Second sentence without a speaker." in transcript
    assert transcript.index("First sentence.") < transcript.index("Second sentence")


def test_write_transcript_artifacts_handles_empty_transcripts(tmp_path) -> None:
    paths = write_transcript_artifacts(
        session_id="empty/session",
        segments=[],
        output_root=tmp_path,
    )

    assert paths.output_dir == tmp_path / "empty_session"
    assert paths.transcript_jsonl_path.read_text(encoding="utf-8") == ""
    transcript = paths.transcript_markdown_path.read_text(encoding="utf-8")
    assert "Session: `empty/session`" in transcript
    assert "Segments: 0" in transcript
    assert "No transcript segments." in transcript


def test_write_transcript_artifacts_sanitizes_session_directory(tmp_path) -> None:
    paths = write_transcript_artifacts(
        session_id="../lecture:private\\session",
        segments=[],
        output_root=tmp_path,
    )

    assert paths.output_dir == tmp_path / "lecture_private_session"
    assert paths.transcript_jsonl_path.parent == paths.output_dir
    assert paths.transcript_markdown_path.parent == paths.output_dir


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
