from __future__ import annotations

import json
import wave
from pathlib import Path
from types import SimpleNamespace

import pytest

from async_scholar.stt import benchmark


def test_run_benchmark_writes_privacy_safe_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    audio_path = tmp_path / "private lecture.wav"
    _write_wav(audio_path, duration_seconds=2.0)
    output_root = tmp_path / "benchmark-output"
    captured: dict[str, object] = {}

    def fake_transcribe_file_to_artifacts(
        audio_path_arg: Path,
        *,
        model_size_or_path: str,
        output_root: Path,
        transcriber_factory: object | None = None,
    ) -> SimpleNamespace:
        captured["audio_path"] = audio_path_arg
        captured["model_size_or_path"] = model_size_or_path
        captured["output_root"] = output_root
        captured["transcriber_factory"] = transcriber_factory

        artifact_dir = Path(output_root) / "file-stt-test-session"
        artifact_dir.mkdir(parents=True)
        transcript_jsonl = artifact_dir / "transcript.jsonl"
        transcript_markdown = artifact_dir / "transcript.md"
        transcript_jsonl.write_text(
            '{"text": "SECRET TRANSCRIPT TEXT"}\n',
            encoding="utf-8",
        )
        transcript_markdown.write_text(
            "SECRET TRANSCRIPT TEXT\n",
            encoding="utf-8",
        )
        return SimpleNamespace(
            session_id="file-stt-test-session",
            segment_count=3,
            artifact_paths=SimpleNamespace(
                output_dir=artifact_dir,
                transcript_jsonl_path=transcript_jsonl,
                transcript_markdown_path=transcript_markdown,
            ),
        )

    monkeypatch.setattr(
        benchmark,
        "transcribe_file_to_artifacts",
        fake_transcribe_file_to_artifacts,
    )
    clock_values = iter([10.0, 13.0])

    result = benchmark.run_benchmark(
        audio_path,
        model_size_or_path=r"C:\Users\student\private-models\faster-whisper-medium",
        output_root=output_root,
        transcriber_factory="stub-factory",
        clock=lambda: next(clock_values),
    )

    assert captured == {
        "audio_path": audio_path,
        "model_size_or_path": (
            r"C:\Users\student\private-models\faster-whisper-medium"
        ),
        "output_root": output_root,
        "transcriber_factory": "stub-factory",
    }
    assert result.report_path == output_root / "file-stt-test-session" / (
        "benchmark-report.json"
    )
    assert result.report_path.exists()

    report = json.loads(result.report_path.read_text(encoding="utf-8"))
    assert report["input"]["audio_file_name"] == "private lecture.wav"
    assert report["input"]["audio_duration_seconds"] == 2.0
    assert report["model"] == {
        "reference": "faster-whisper-medium",
        "path_like_reference_redacted": True,
    }
    assert report["timing"]["elapsed_seconds"] == 3.0
    assert report["timing"]["real_time_factor"] == 1.5
    assert report["transcript"] == {
        "session_id": "file-stt-test-session",
        "segment_count": 3,
    }
    assert report["artifacts"] == {
        "output_dir": ".",
        "transcript_jsonl": "transcript.jsonl",
        "transcript_markdown": "transcript.md",
        "benchmark_report": "benchmark-report.json",
    }
    assert report["unavailable_metrics"]["peak_ram_bytes"]["value"] is None

    report_text = result.report_path.read_text(encoding="utf-8")
    assert "SECRET TRANSCRIPT TEXT" not in report_text
    assert str(audio_path) not in report_text
    assert str(tmp_path) not in report_text
    assert "private-models" not in report_text


def test_run_benchmark_marks_duration_and_rtf_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    audio_path = tmp_path / "sample.bin"
    audio_path.write_bytes(b"not a wav")
    output_root = tmp_path / "benchmark-output"

    def fake_transcribe_file_to_artifacts(
        audio_path_arg: Path,
        *,
        model_size_or_path: str,
        output_root: Path,
        transcriber_factory: object | None = None,
    ) -> SimpleNamespace:
        del audio_path_arg, model_size_or_path, transcriber_factory
        artifact_dir = Path(output_root) / "file-stt-test-session"
        artifact_dir.mkdir(parents=True)
        transcript_jsonl = artifact_dir / "transcript.jsonl"
        transcript_markdown = artifact_dir / "transcript.md"
        transcript_jsonl.write_text("", encoding="utf-8")
        transcript_markdown.write_text("", encoding="utf-8")
        return SimpleNamespace(
            session_id="file-stt-test-session",
            segment_count=0,
            artifact_paths=SimpleNamespace(
                output_dir=artifact_dir,
                transcript_jsonl_path=transcript_jsonl,
                transcript_markdown_path=transcript_markdown,
            ),
        )

    monkeypatch.setattr(
        benchmark,
        "transcribe_file_to_artifacts",
        fake_transcribe_file_to_artifacts,
    )
    clock_values = iter([1.0, 4.0])

    result = benchmark.run_benchmark(
        audio_path,
        model_size_or_path="tiny",
        output_root=output_root,
        clock=lambda: next(clock_values),
    )

    report = json.loads(result.report_path.read_text(encoding="utf-8"))
    assert report["input"]["audio_duration_seconds"] is None
    assert report["input"]["audio_duration_status"] == "unavailable"
    assert report["timing"]["real_time_factor"] is None


def test_cli_requires_explicit_arguments() -> None:
    parser = benchmark._build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args([])

    assert exc_info.value.code == 2


def _write_wav(path: Path, *, duration_seconds: float) -> None:
    frame_rate = 8_000
    frame_count = int(frame_rate * duration_seconds)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(frame_rate)
        wav_file.writeframes(b"\0\0" * frame_count)
