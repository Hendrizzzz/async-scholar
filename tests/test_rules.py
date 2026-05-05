from pathlib import Path

from async_scholar.fixtures import load_transcript_fixture
from async_scholar.rules import detect_events
from async_scholar.schemas import TranscriptSegment

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "transcripts"


def test_detect_events_finds_attendance_prompt_from_fixture() -> None:
    segments = load_transcript_fixture(FIXTURE_DIR / "attendance_roll_call.jsonl")

    events = detect_events(segments)

    assert len(events) == 2
    assert (
        events[0].event_id
        == "fixture:attendance_roll_call:event:0001:attendance_prompt"
    )
    assert events[0].session_id == "fixture:attendance_roll_call"
    assert events[0].event_type == "attendance_prompt"
    assert events[0].detected_at_seconds == 0.0
    assert events[0].source_segment_ids == (
        "fixture:attendance_roll_call:segment:0001",
    )
    assert events[0].message == "Attendance prompt detected."
    assert 0 <= events[0].confidence <= 1
    assert (
        events[1].event_id
        == "fixture:attendance_roll_call:event:0002:attendance_prompt"
    )


def test_detect_events_ignores_casual_name_mentions() -> None:
    segments = load_transcript_fixture(FIXTURE_DIR / "casual_name_mention.jsonl")

    events = detect_events(segments)

    assert events == []


def test_detect_events_finds_participation_cues_from_fixture() -> None:
    segments = load_transcript_fixture(FIXTURE_DIR / "participation_cues.jsonl")

    events = detect_events(segments)

    assert [event.event_id for event in events] == [
        "fixture:participation_cues:event:0001:name_call",
        "fixture:participation_cues:event:0002:direct_question",
        "fixture:participation_cues:event:0003:camera_mic_request",
        "fixture:participation_cues:event:0004:quiz_prompt",
    ]
    assert [event.event_type for event in events] == [
        "name_call",
        "direct_question",
        "camera_mic_request",
        "quiz_prompt",
    ]
    assert [event.detected_at_seconds for event in events] == [
        0.0,
        8.0,
        16.0,
        24.0,
    ]
    assert [event.source_segment_ids for event in events] == [
        ("fixture:participation_cues:segment:0001",),
        ("fixture:participation_cues:segment:0002",),
        ("fixture:participation_cues:segment:0003",),
        ("fixture:participation_cues:segment:0004",),
    ]
    assert [event.message for event in events] == [
        "Name call detected.",
        "Direct question detected.",
        "Camera or microphone request detected.",
        "Quiz prompt detected.",
    ]
    assert all(0 <= event.confidence <= 1 for event in events)


def test_detect_events_finds_task_prompt() -> None:
    segment = _segment(
        text="Please submit your worksheet in the learning portal after discussion.",
        start_seconds=42.0,
    )

    events = detect_events([segment])

    assert len(events) == 1
    assert events[0].event_type == "task_prompt"
    assert events[0].detected_at_seconds == 42.0
    assert events[0].source_segment_ids == ("session-1:segment:0001",)
    assert events[0].message == "Task or action prompt detected."
    assert 0 <= events[0].confidence <= 1


def test_detect_events_finds_deadline_mention() -> None:
    segment = _segment(
        text="The reflection is due by 5 pm before our next class.",
        start_seconds=120.0,
    )

    events = detect_events([segment])

    assert len(events) == 1
    assert events[0].event_id == "session-1:event:0001:deadline_mention"
    assert events[0].event_type == "deadline_mention"
    assert events[0].detected_at_seconds == 120.0
    assert events[0].message == "Deadline mention detected."
    assert 0 <= events[0].confidence <= 1


def test_detect_events_finds_dismissal_cue() -> None:
    segment = _segment(
        text="That's all for today. Class dismissed.",
        start_seconds=2700.0,
    )

    events = detect_events([segment])

    assert len(events) == 1
    assert events[0].event_id == "session-1:event:0001:dismissal_cue"
    assert events[0].event_type == "dismissal_cue"
    assert events[0].detected_at_seconds == 2700.0
    assert events[0].message == "Dismissal or end-of-class cue detected."
    assert 0 <= events[0].confidence <= 1


def test_detect_events_event_ids_are_deterministic_for_same_order() -> None:
    segments = [
        _segment(
            text="Please submit your notes before midnight.",
            start_seconds=20.0,
            segment_number=1,
        ),
        _segment(
            text="We'll stop here. See you next time.",
            start_seconds=50.0,
            segment_number=2,
        ),
    ]

    first_run = detect_events(segments)
    second_run = detect_events(segments)

    assert [event.event_id for event in first_run] == [
        event.event_id for event in second_run
    ]
    assert [event.event_type for event in first_run] == [
        "task_prompt",
        "deadline_mention",
        "dismissal_cue",
    ]


def _segment(
    *,
    text: str,
    start_seconds: float = 0.0,
    segment_number: int = 1,
) -> TranscriptSegment:
    return TranscriptSegment(
        segment_id=f"session-1:segment:{segment_number:04d}",
        session_id="session-1",
        start_seconds=start_seconds,
        end_seconds=start_seconds + 3.0,
        text=text,
        speaker="instructor",
    )
