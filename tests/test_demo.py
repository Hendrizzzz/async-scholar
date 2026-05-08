from __future__ import annotations

import json
from pathlib import Path

from async_scholar.demo import SessionStatusSnapshot, run_fixture_demo


def test_run_fixture_demo_writes_expected_artifacts(tmp_path) -> None:
    fixture_path = Path("tests/fixtures/transcripts/attendance_roll_call.jsonl")

    result = run_fixture_demo(fixture_path, output_root=tmp_path)

    output_dir = tmp_path / "fixture_attendance_roll_call"
    assert result.session_id == "fixture:attendance_roll_call"
    assert result.segment_count == 5
    assert result.event_count == 2
    assert result.artifact_paths.output_dir == output_dir
    assert result.artifact_paths.events_path == output_dir / "events.jsonl"
    assert result.artifact_paths.alerts_path == output_dir / "alerts.log"
    assert result.artifact_paths.reviewer_path == output_dir / "reviewer.md"

    event_lines = result.artifact_paths.events_path.read_text(
        encoding="utf-8"
    ).splitlines()
    alert_lines = result.artifact_paths.alerts_path.read_text(
        encoding="utf-8"
    ).splitlines()
    reviewer = result.artifact_paths.reviewer_path.read_text(encoding="utf-8")

    assert len(event_lines) == 2
    assert len(alert_lines) == 2
    assert json.loads(event_lines[0])["event_type"] == "attendance_prompt"
    assert json.loads(alert_lines[0])["requires_confirmation"] is True
    assert "Good morning, everyone. I am going to take attendance" in reviewer
    assert "When I call your name, please say present" in reviewer
    assert "Here, professor." not in reviewer


def test_run_fixture_demo_exposes_safe_status_snapshot(tmp_path) -> None:
    fixture_path = Path("tests/fixtures/transcripts/attendance_roll_call.jsonl")

    result = run_fixture_demo(fixture_path, output_root=tmp_path)
    snapshot = result.status_snapshot

    assert isinstance(snapshot, SessionStatusSnapshot)
    assert snapshot.session_id == "fixture:attendance_roll_call"
    assert snapshot.source_kind == "fixture_demo"
    assert snapshot.run_status == "completed"
    assert snapshot.segment_count == 5
    assert snapshot.event_count == 2
    assert snapshot.artifact_paths == result.artifact_paths
    assert snapshot.artifact_paths.output_dir == result.artifact_paths.output_dir
    assert snapshot.artifact_paths.events_path == result.artifact_paths.events_path
    assert snapshot.artifact_paths.alerts_path == result.artifact_paths.alerts_path
    assert snapshot.artifact_paths.reviewer_path == result.artifact_paths.reviewer_path


def test_status_snapshot_keeps_private_contents_out_of_contract(tmp_path) -> None:
    fixture_path = Path("tests/fixtures/transcripts/attendance_roll_call.jsonl")

    snapshot = run_fixture_demo(fixture_path, output_root=tmp_path).status_snapshot

    assert set(SessionStatusSnapshot.__dataclass_fields__) == {
        "session_id",
        "source_kind",
        "run_status",
        "segment_count",
        "event_count",
        "artifact_paths",
    }
    assert not hasattr(snapshot, "segments")
    assert not hasattr(snapshot, "events")
    assert not hasattr(snapshot, "alerts")
    assert not hasattr(snapshot, "source_segment_ids")

    safe_status_values = {
        "session_id": snapshot.session_id,
        "source_kind": snapshot.source_kind,
        "run_status": snapshot.run_status,
        "segment_count": snapshot.segment_count,
        "event_count": snapshot.event_count,
    }
    safe_status_text = json.dumps(safe_status_values, sort_keys=True)

    assert (
        "Good morning, everyone. I am going to take attendance" not in safe_status_text
    )
    assert "When I call your name, please say present" not in safe_status_text
    assert "Here, professor." not in safe_status_text
    assert "source_segment_id" not in safe_status_text
    assert "requires_confirmation" not in safe_status_text
