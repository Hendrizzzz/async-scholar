from __future__ import annotations

import importlib
import sys
import types
import wave
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StubWhisperSegment:
    start: float
    end: float
    text: str


class StubWhisperModel:
    instances: list[StubWhisperModel] = []

    def __init__(
        self,
        model_size_or_path: str,
        *,
        device: str,
        compute_type: str,
    ) -> None:
        self.model_size_or_path = model_size_or_path
        self.device = device
        self.compute_type = compute_type
        self.audio_inputs: list[str] = []
        StubWhisperModel.instances.append(self)

    def transcribe(self, audio_input: str):
        self.audio_inputs.append(audio_input)
        return (
            [
                StubWhisperSegment(0.0, 1.25, " first segment "),
                StubWhisperSegment(1.25, 1.5, "   "),
                StubWhisperSegment(1.5, 3.0, "second segment"),
            ],
            object(),
        )


def test_stt_import_does_not_import_faster_whisper() -> None:
    sys.modules.pop("faster_whisper", None)

    stt_module = importlib.import_module("async_scholar.stt")

    assert stt_module.FasterWhisperTranscriber
    assert "faster_whisper" not in sys.modules


def test_transcribe_maps_faster_whisper_segments_from_path(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _install_stub_faster_whisper(monkeypatch)
    from async_scholar.stt import FasterWhisperTranscriber

    audio_path = tmp_path / "lecture.wav"
    transcriber = FasterWhisperTranscriber("local-model")

    segments = transcriber.transcribe(audio_path)
    repeated_segments = transcriber.transcribe(str(audio_path))

    assert len(StubWhisperModel.instances) == 1
    assert StubWhisperModel.instances[0].model_size_or_path == "local-model"
    assert StubWhisperModel.instances[0].device == "cpu"
    assert StubWhisperModel.instances[0].compute_type == "int8"
    assert StubWhisperModel.instances[0].audio_inputs == [
        str(audio_path),
        str(audio_path),
    ]

    assert [segment.text for segment in segments] == [
        "first segment",
        "second segment",
    ]
    assert [segment.start_seconds for segment in segments] == [0.0, 1.5]
    assert [segment.end_seconds for segment in segments] == [1.25, 3.0]
    assert {segment.session_id for segment in segments} == {segments[0].session_id}
    assert [segment.segment_id for segment in repeated_segments] == [
        segment.segment_id for segment in segments
    ]
    assert all(
        segment.segment_id.startswith(f"{segment.session_id}_seg_")
        for segment in segments
    )


def test_transcribe_accepts_file_audio_source(monkeypatch, tmp_path: Path) -> None:
    _install_stub_faster_whisper(monkeypatch)
    from async_scholar.audio import FileAudioSource
    from async_scholar.stt import FasterWhisperTranscriber

    audio_path = tmp_path / "lecture.wav"
    _write_tiny_wav(audio_path)

    source = FileAudioSource(audio_path)
    segments = FasterWhisperTranscriber("local-model").transcribe(source)

    assert len(segments) == 2
    assert StubWhisperModel.instances[0].audio_inputs == [str(source.metadata.path)]


def test_model_size_or_path_is_required() -> None:
    from async_scholar.stt import FasterWhisperTranscriber

    try:
        FasterWhisperTranscriber("   ")
    except ValueError as error:
        assert "model_size_or_path" in str(error)
    else:
        raise AssertionError("expected model_size_or_path validation")


def _install_stub_faster_whisper(monkeypatch) -> None:
    StubWhisperModel.instances.clear()
    module = types.ModuleType("faster_whisper")
    module.WhisperModel = StubWhisperModel
    monkeypatch.setitem(sys.modules, "faster_whisper", module)


def _write_tiny_wav(path: Path) -> None:
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16_000)
        wav_file.writeframes(b"\x00\x00" * 16)
