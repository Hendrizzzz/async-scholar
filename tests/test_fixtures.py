from pathlib import Path

import pytest

from async_scholar.fixtures import load_transcript_fixture
from async_scholar.schemas import TranscriptSegment

TRANSCRIPT_FIXTURES = Path(__file__).parent / "fixtures" / "transcripts"


def test_loads_valid_attendance_roll_call_fixture() -> None:
    segments = load_transcript_fixture(
        TRANSCRIPT_FIXTURES / "attendance_roll_call.jsonl"
    )

    assert all(isinstance(segment, TranscriptSegment) for segment in segments)
    assert [segment.speaker for segment in segments] == [
        "instructor",
        "instructor",
        "student",
        "instructor",
        "student",
    ]
    assert segments[0].start_seconds == 0.0
    assert segments[-1].end_seconds == 13.0
    assert "present" in segments[2].text.lower()


def test_loads_valid_casual_name_mention_fixture() -> None:
    segments = load_transcript_fixture(
        TRANSCRIPT_FIXTURES / "casual_name_mention.jsonl"
    )

    assert len(segments) == 4
    assert {segment.session_id for segment in segments} == {
        "fixture:casual_name_mention"
    }
    assert any("Jordan" in segment.text for segment in segments)
    assert all("attendance" not in segment.text.lower() for segment in segments)


def test_fixture_segment_and_session_ids_are_deterministic() -> None:
    first_load = load_transcript_fixture(
        TRANSCRIPT_FIXTURES / "attendance_roll_call.jsonl"
    )
    second_load = load_transcript_fixture(
        TRANSCRIPT_FIXTURES / "attendance_roll_call.jsonl"
    )

    expected_ids = [
        "fixture:attendance_roll_call:segment:0001",
        "fixture:attendance_roll_call:segment:0002",
        "fixture:attendance_roll_call:segment:0003",
        "fixture:attendance_roll_call:segment:0004",
        "fixture:attendance_roll_call:segment:0005",
    ]
    assert [segment.session_id for segment in first_load] == [
        "fixture:attendance_roll_call"
    ] * 5
    assert [segment.segment_id for segment in first_load] == expected_ids
    assert [segment.segment_id for segment in second_load] == expected_ids


def test_loader_surfaces_schema_validation_failures(tmp_path: Path) -> None:
    invalid_fixture = tmp_path / "invalid_start.jsonl"
    invalid_fixture.write_text(
        '{"start_s": -1.0, "end_s": 2.0, "text": "bad start"}\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="line 1"):
        load_transcript_fixture(invalid_fixture)


def test_loader_rejects_malformed_jsonl(tmp_path: Path) -> None:
    malformed_fixture = tmp_path / "malformed.jsonl"
    malformed_fixture.write_text(
        '{"start_s": 0.0, "end_s": 1.0, "text": "ok"}\n{"start_s": 1.0',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="line 2"):
        load_transcript_fixture(malformed_fixture)
