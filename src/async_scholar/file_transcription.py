"""File transcription orchestration for local transcript artifacts."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from async_scholar.artifacts import TranscriptArtifactPaths, write_transcript_artifacts
from async_scholar.audio.chunking import (
    SttChunkWindow,
    VadChunkingConfig,
    aggregate_speech_windows,
)
from async_scholar.audio.vad import SpeechWindow
from async_scholar.schemas import TranscriptSegment


class FileTranscriber(Protocol):
    def transcribe(self, audio_source: str | Path) -> Sequence[TranscriptSegment]:
        """Transcribe one local audio source into transcript segments."""


TranscriberFactory = Callable[[str], FileTranscriber]
SpeechDetector = Callable[[Path], Iterable[SpeechWindow]]


@dataclass(frozen=True)
class FileTranscriptionResult:
    session_id: str
    segment_count: int
    artifact_paths: TranscriptArtifactPaths


def plan_file_transcription_chunks(
    audio_path: str | Path,
    *,
    speech_detector: SpeechDetector | None = None,
    audio_duration_seconds: float | None = None,
    chunking_config: VadChunkingConfig | None = None,
) -> list[SttChunkWindow]:
    """Plan deterministic STT chunk windows for one existing local audio file."""
    audio_file = Path(audio_path)
    if not audio_file.is_file():
        raise FileNotFoundError(audio_file)

    detector = speech_detector or _detect_speech_windows
    speech_windows = detector(audio_file)
    return aggregate_speech_windows(
        speech_windows,
        audio_duration_seconds=audio_duration_seconds,
        config=chunking_config,
    )


def transcribe_file_to_artifacts(
    audio_path: str | Path,
    *,
    model_size_or_path: str,
    output_root: str | Path,
    transcriber_factory: TranscriberFactory | None = None,
) -> FileTranscriptionResult:
    """Transcribe a local audio file and write transcript artifacts."""
    model_reference = model_size_or_path.strip()
    if not model_reference:
        raise ValueError("model_size_or_path must be explicit")

    audio_file = Path(audio_path)
    if not audio_file.is_file():
        raise FileNotFoundError(audio_file)

    factory = transcriber_factory or _build_faster_whisper_transcriber
    transcriber = factory(model_reference)
    segments = tuple(transcriber.transcribe(audio_file))
    session_id = _artifact_session_id(audio_file, segments)
    artifact_paths = write_transcript_artifacts(
        session_id=session_id,
        segments=segments,
        output_root=output_root,
    )

    return FileTranscriptionResult(
        session_id=session_id,
        segment_count=len(segments),
        artifact_paths=artifact_paths,
    )


def _build_faster_whisper_transcriber(model_size_or_path: str) -> FileTranscriber:
    from async_scholar.stt import FasterWhisperTranscriber

    return FasterWhisperTranscriber(model_size_or_path=model_size_or_path)


def _detect_speech_windows(audio_path: Path) -> list[SpeechWindow]:
    from async_scholar.audio.vad import detect_speech_windows

    return detect_speech_windows(audio_path)


def _artifact_session_id(
    audio_path: Path,
    segments: Sequence[TranscriptSegment],
) -> str:
    if segments:
        return segments[0].session_id

    return _deterministic_empty_transcript_session_id(audio_path)


def _deterministic_empty_transcript_session_id(audio_path: Path) -> str:
    resolved = str(audio_path.resolve(strict=False))
    digest = hashlib.sha256(resolved.encode("utf-8")).hexdigest()[:12]
    return f"file-stt-{digest}"


__all__ = [
    "FileTranscriber",
    "FileTranscriptionResult",
    "SpeechDetector",
    "TranscriberFactory",
    "plan_file_transcription_chunks",
    "transcribe_file_to_artifacts",
]
