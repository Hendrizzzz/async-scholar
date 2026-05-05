from __future__ import annotations

from pathlib import Path

import pytest

from async_scholar.file_transcription import transcribe_file_to_artifacts
from async_scholar.schemas import TranscriptSegment


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
