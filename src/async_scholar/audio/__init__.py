"""Audio file helpers for AsyncScholar."""

from async_scholar.audio.chunking import (
    DEFAULT_VAD_CHUNKING_CONFIG,
    SttChunkWindow,
    VadChunkingConfig,
    aggregate_speech_windows,
)
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
    "DEFAULT_VAD_CHUNKING_CONFIG",
    "FileAudioSource",
    "InvalidVadTimestampError",
    "InvalidWavFileError",
    "SileroVadDetector",
    "SpeechWindow",
    "SttChunkWindow",
    "VadChunkingConfig",
    "aggregate_speech_windows",
    "detect_speech_windows",
    "speech_windows_from_timestamps",
]
