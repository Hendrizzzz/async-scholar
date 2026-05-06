from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from async_scholar.audio.vad_plan_demo import REPORT_FILENAME, run_vad_plan_demo


@dataclass(frozen=True)
class FakeWindow:
    start_seconds: float
    end_seconds: float


def test_vad_plan_report_generation_is_privacy_safe(tmp_path: Path) -> None:
    audio_path = tmp_path / "private-class-session-secret.wav"
    output_root = tmp_path / "demo-output"
    audio_path.write_bytes(b"not real audio")

    def speech_detector(path: Path) -> list[FakeWindow]:
        assert path == audio_path
        return [FakeWindow(1.0, 2.5), FakeWindow(5.0, 7.0)]

    def chunk_planner(path: Path, *, speech_detector: object) -> list[FakeWindow]:
        assert path == audio_path
        speech_detector(path)
        return [FakeWindow(0.5, 8.0)]

    report_path = run_vad_plan_demo(
        audio_path,
        output_root,
        speech_detector=speech_detector,
        chunk_planner=chunk_planner,
    )

    report = json.loads(report_path.read_text())
    report_text = json.dumps(report)

    assert report_path == output_root / REPORT_FILENAME
    assert report["report_name"] == REPORT_FILENAME
    assert report["artifact_names"] == [REPORT_FILENAME]
    assert report["speech"]["count"] == 2
    assert report["speech"]["total_duration_seconds"] == 3.5
    assert report["chunks"]["count"] == 1
    assert report["chunks"]["queued_audio_seconds"] == 7.5
    assert report["chunks"]["timing_windows"] == [
        {"duration_seconds": 7.5, "end_seconds": 8.0, "start_seconds": 0.5}
    ]
    assert str(audio_path) not in report_text
    assert audio_path.name not in report_text
    assert str(output_root) not in report_text
    assert "secret" not in report_text


def test_vad_plan_report_handles_empty_speech_and_chunks(tmp_path: Path) -> None:
    audio_path = tmp_path / "empty.wav"
    output_root = tmp_path / "out"
    audio_path.write_bytes(b"")

    def speech_detector(path: Path) -> list[FakeWindow]:
        return []

    def chunk_planner(path: Path, *, speech_detector: object) -> list[FakeWindow]:
        speech_detector(path)
        return []

    report_path = run_vad_plan_demo(
        audio_path,
        output_root,
        speech_detector=speech_detector,
        chunk_planner=chunk_planner,
    )

    report = json.loads(report_path.read_text())

    assert report["speech"] == {
        "count": 0,
        "first_start_seconds": None,
        "last_end_seconds": None,
        "max_duration_seconds": None,
        "min_duration_seconds": None,
        "total_duration_seconds": 0.0,
    }
    assert report["chunks"]["count"] == 0
    assert report["chunks"]["queued_audio_seconds"] == 0.0
    assert report["chunks"]["timing_windows"] == []
    assert report["backpressure"] == {"diagnostic": None, "evaluated": False}


def test_vad_plan_report_includes_backpressure_diagnostic(
    tmp_path: Path,
) -> None:
    audio_path = tmp_path / "lecture.wav"
    output_root = tmp_path / "out"
    audio_path.write_bytes(b"fake")

    def speech_detector(path: Path) -> list[FakeWindow]:
        return [FakeWindow(0.0, 1.0)]

    def chunk_planner(path: Path, *, speech_detector: object) -> list[FakeWindow]:
        speech_detector(path)
        return [FakeWindow(0.0, 8.0), FakeWindow(8.0, 12.0)]

    report_path = run_vad_plan_demo(
        audio_path,
        output_root,
        speech_detector=speech_detector,
        chunk_planner=chunk_planner,
        oldest_pending_age_seconds=10.0,
        observed_at_seconds=42.0,
    )

    report = json.loads(report_path.read_text())

    assert report["backpressure"]["evaluated"] is True
    assert report["backpressure"]["diagnostic"] == {
        "oldest_pending_age_seconds": 10.0,
        "observed_at_seconds": 42.0,
        "pending_chunk_count": 2,
        "queued_audio_seconds": 12.0,
        "recommended_action": "pause_file_input",
        "sustained_backlog_threshold_seconds": 10.0,
    }


def test_vad_plan_report_path_is_deterministic_under_explicit_root(
    tmp_path: Path,
) -> None:
    audio_path = tmp_path / "input.wav"
    output_root = tmp_path / "explicit" / "root"
    audio_path.write_bytes(b"fake")

    def speech_detector(path: Path) -> list[FakeWindow]:
        return []

    def chunk_planner(path: Path, *, speech_detector: object) -> list[FakeWindow]:
        return [FakeWindow(2.0, 3.25)]

    first_path = run_vad_plan_demo(
        audio_path,
        output_root,
        speech_detector=speech_detector,
        chunk_planner=chunk_planner,
    )
    second_path = run_vad_plan_demo(
        audio_path,
        output_root,
        speech_detector=speech_detector,
        chunk_planner=chunk_planner,
    )

    assert first_path == second_path == output_root / REPORT_FILENAME
    assert json.loads(second_path.read_text())["chunks"]["timing_windows"] == [
        {"duration_seconds": 1.25, "end_seconds": 3.25, "start_seconds": 2.0}
    ]
