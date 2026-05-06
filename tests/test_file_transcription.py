from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

from async_scholar.audio import SpeechWindow, VadChunkingConfig
from async_scholar.audio.chunking import SttChunkWindow
from async_scholar.file_transcription import (
    plan_file_transcription_chunks,
    transcribe_file_to_artifacts,
)
from async_scholar.schemas import TranscriptSegment


def test_file_transcription_import_does_not_import_silero_vad() -> None:
    sys.modules.pop("silero_vad", None)
    sys.modules.pop("async_scholar.file_transcription", None)

    module = importlib.import_module("async_scholar.file_transcription")

    assert "silero_vad" not in sys.modules
    assert module.plan_file_transcription_chunks.__name__ == (
        "plan_file_transcription_chunks"
    )


def test_plan_file_transcription_chunks_uses_detector_path_and_default_aggregation(
    tmp_path,
) -> None:
    audio_path = tmp_path / "lecture.wav"
    audio_path.write_bytes(b"stub audio")
    received_paths: list[Path] = []

    def detector(path: Path) -> list[SpeechWindow]:
        received_paths.append(path)
        return [SpeechWindow(start_seconds=1.0, end_seconds=2.0)]

    chunks = plan_file_transcription_chunks(
        str(audio_path),
        speech_detector=detector,
    )

    assert received_paths == [audio_path]
    assert len(chunks) == 1
    assert_chunk(chunks[0], 0.5, 8.5)
    assert chunks[0].duration_seconds == pytest.approx(8.0)


def test_plan_file_transcription_chunks_returns_no_chunks_for_empty_speech(
    tmp_path,
) -> None:
    audio_path = tmp_path / "silence.wav"
    audio_path.write_bytes(b"stub audio")

    chunks = plan_file_transcription_chunks(
        audio_path,
        speech_detector=lambda _path: [],
    )

    assert chunks == []


def test_plan_file_transcription_chunks_honors_explicit_chunking_config(
    tmp_path,
) -> None:
    audio_path = tmp_path / "lecture.wav"
    audio_path.write_bytes(b"stub audio")
    config = VadChunkingConfig(
        pre_roll_seconds=0.0,
        post_roll_seconds=0.0,
        minimum_window_seconds=0.0,
    )

    chunks = plan_file_transcription_chunks(
        audio_path,
        speech_detector=lambda _path: [
            SpeechWindow(start_seconds=2.0, end_seconds=4.0)
        ],
        chunking_config=config,
    )

    assert len(chunks) == 1
    assert_chunk(chunks[0], 2.0, 4.0)


def test_plan_file_transcription_chunks_passes_audio_duration_for_clamping(
    tmp_path,
) -> None:
    audio_path = tmp_path / "lecture.wav"
    audio_path.write_bytes(b"stub audio")

    chunks = plan_file_transcription_chunks(
        audio_path,
        speech_detector=lambda _path: [
            SpeechWindow(start_seconds=6.0, end_seconds=9.8)
        ],
        audio_duration_seconds=10.0,
    )

    assert len(chunks) == 1
    assert_chunk(chunks[0], 2.0, 10.0)


@pytest.mark.parametrize("path_name", ["missing.wav", "lecture_dir"])
def test_plan_file_transcription_chunks_requires_existing_audio_file(
    tmp_path,
    path_name: str,
) -> None:
    audio_path = tmp_path / path_name
    if path_name == "lecture_dir":
        audio_path.mkdir()

    with pytest.raises(FileNotFoundError, match=path_name):
        plan_file_transcription_chunks(
            audio_path,
            speech_detector=lambda _path: [],
        )


def test_transcribe_file_to_artifacts_uses_stub_and_writes_outputs(tmp_path) -> None:
    audio_path = tmp_path / "lecture.wav"
    audio_path.write_bytes(b"stub audio")
    output_root = tmp_path / "out"
    stub = _StubTranscriber(
        [
            TranscriptSegment(
                segment_id="session:one:segment:0001",
                session_id="session:one/week 1",
                start_seconds=0.0,
                end_seconds=2.0,
                text="Welcome to class.",
                speaker="instructor",
            )
        ]
    )
    created_models: list[str] = []

    def factory(model_size_or_path: str) -> _StubTranscriber:
        created_models.append(model_size_or_path)
        return stub

    result = transcribe_file_to_artifacts(
        audio_path,
        model_size_or_path="tiny.en",
        output_root=output_root,
        transcriber_factory=factory,
    )

    assert created_models == ["tiny.en"]
    assert stub.audio_sources == [audio_path]
    assert result.session_id == "session:one/week 1"
    assert result.segment_count == 1
    assert result.artifact_paths.output_dir == output_root / "session_one_week_1"
    jsonl_text = result.artifact_paths.transcript_jsonl_path.read_text(encoding="utf-8")
    markdown_text = result.artifact_paths.transcript_markdown_path.read_text(
        encoding="utf-8"
    )
    assert "Welcome to class." in jsonl_text
    assert "Session: `session:one/week 1`" in markdown_text
    assert "**instructor:** Welcome to class." in markdown_text


def test_transcribe_file_to_artifacts_empty_transcript_is_deterministic(
    tmp_path,
) -> None:
    audio_path = tmp_path / "silence.wav"
    audio_path.write_bytes(b"")
    first_output_root = tmp_path / "first"
    second_output_root = tmp_path / "second"

    first_result = transcribe_file_to_artifacts(
        audio_path,
        model_size_or_path="tiny",
        output_root=first_output_root,
        transcriber_factory=lambda _model: _StubTranscriber([]),
    )
    second_result = transcribe_file_to_artifacts(
        audio_path,
        model_size_or_path="tiny",
        output_root=second_output_root,
        transcriber_factory=lambda _model: _StubTranscriber([]),
    )

    assert first_result.session_id == second_result.session_id
    assert first_result.session_id.startswith("file-stt-")
    assert first_result.segment_count == 0
    assert (
        first_result.artifact_paths.transcript_jsonl_path.read_text(encoding="utf-8")
        == ""
    )
    transcript = first_result.artifact_paths.transcript_markdown_path.read_text(
        encoding="utf-8"
    )
    assert f"Session: `{first_result.session_id}`" in transcript
    assert "Segments: 0" in transcript
    assert "No transcript segments." in transcript


def test_transcribe_file_to_artifacts_requires_existing_audio_file(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        transcribe_file_to_artifacts(
            tmp_path / "missing.wav",
            model_size_or_path="tiny",
            output_root=tmp_path / "out",
            transcriber_factory=lambda _model: _StubTranscriber([]),
        )


def test_transcribe_file_to_artifacts_requires_explicit_model(tmp_path) -> None:
    audio_path = tmp_path / "lecture.wav"
    audio_path.write_bytes(b"stub audio")

    with pytest.raises(ValueError, match="model_size_or_path"):
        transcribe_file_to_artifacts(
            audio_path,
            model_size_or_path=" ",
            output_root=tmp_path / "out",
            transcriber_factory=lambda _model: _StubTranscriber([]),
        )


class _StubTranscriber:
    def __init__(self, segments: list[TranscriptSegment]) -> None:
        self._segments = segments
        self.audio_sources: list[str | Path] = []

    def transcribe(self, audio_source: str | Path) -> list[TranscriptSegment]:
        self.audio_sources.append(audio_source)
        return self._segments


def assert_chunk(
    chunk: SttChunkWindow,
    start_seconds: float,
    end_seconds: float,
) -> None:
    assert chunk.start_seconds == pytest.approx(start_seconds)
    assert chunk.end_seconds == pytest.approx(end_seconds)
