"""Minimal speech-to-text transcriber boundary."""

from pathlib import Path
from typing import Protocol, TypeAlias

from async_scholar.audio import FileAudioSource
from async_scholar.schemas import TranscriptSegment

AudioInput: TypeAlias = FileAudioSource | str | Path


class Transcriber(Protocol):
    """Boundary for turning WAV audio input into transcript segments."""

    def transcribe(self, source: AudioInput) -> list[TranscriptSegment]:
        """Return transcript segments for a WAV source."""
