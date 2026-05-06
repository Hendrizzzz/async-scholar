"""Audio file helpers for AsyncScholar."""

from async_scholar.audio.file_source import (
    AudioChunk,
    AudioMetadata,
    FileAudioSource,
    InvalidWavFileError,
)
from async_scholar.audio.vad import (
    InvalidVadTimestampError,
    SileroVadDetector,
    SpeechWindow,
    detect_speech_windows,
    speech_windows_from_timestamps,
)

__all__ = [
    "AudioChunk",
    "AudioMetadata",
    "FileAudioSource",
    "InvalidVadTimestampError",
    "InvalidWavFileError",
    "SileroVadDetector",
    "SpeechWindow",
    "detect_speech_windows",
    "speech_windows_from_timestamps",
]
