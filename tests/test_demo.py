from __future__ import annotations

import json
from pathlib import Path

from async_scholar.demo import run_fixture_demo


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
