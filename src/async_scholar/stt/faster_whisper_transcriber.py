"""Faster-whisper backed file transcriber."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from async_scholar.audio import FileAudioSource
from async_scholar.schemas import TranscriptSegment
from async_scholar.stt.transcriber import AudioInput


class FasterWhisperTranscriber:
    """Transcribe local audio files with faster-whisper on conservative defaults."""

    def __init__(
        self,
        model_size_or_path: str | Path,
        *,
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:
        model_reference = str(model_size_or_path)
        if not model_reference.strip():
            msg = "model_size_or_path must be provided explicitly"
            raise ValueError(msg)

        self.model_size_or_path = model_reference
        self.device = device
        self.compute_type = compute_type
        self._model: Any | None = None

    def transcribe(self, source: AudioInput) -> list[TranscriptSegment]:
        audio_path = _audio_path(source)
        session_id = self._session_id(audio_path)
        raw_segments, _info = self._model_instance().transcribe(str(audio_path))

        segments: list[TranscriptSegment] = []
        for index, raw_segment in enumerate(raw_segments):
            text = str(getattr(raw_segment, "text", "")).strip()
            if not text:
                continue

            segments.append(
                TranscriptSegment(
                    segment_id=f"{session_id}_seg_{index:04d}",
                    session_id=session_id,
                    start_seconds=float(raw_segment.start),
                    end_seconds=float(raw_segment.end),
                    text=text,
                )
            )

        return segments

    def _model_instance(self) -> Any:
        if self._model is None:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                self.model_size_or_path,
                device=self.device,
                compute_type=self.compute_type,
            )
        return self._model

    def _session_id(self, audio_path: Path) -> str:
        stable_path = audio_path.resolve(strict=False)
        identity = f"{stable_path}|{self.model_size_or_path}"
        digest = sha256(identity.encode("utf-8")).hexdigest()[:16]
        return f"faster_whisper_{digest}"


def _audio_path(source: AudioInput) -> Path:
    if isinstance(source, FileAudioSource):
        return Path(source.metadata.path)
    return Path(source)
