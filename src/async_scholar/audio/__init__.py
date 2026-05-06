"""Audio file helpers for AsyncScholar."""

from async_scholar.audio.backpressure import (
    DEFAULT_BACKPRESSURE_CONFIG,
    DEFAULT_SUSTAINED_BACKLOG_THRESHOLD_SECONDS,
    FILE_INPUT_BACKPRESSURE_RECOMMENDATION,
    AudioBackpressureDiagnostic,
    BackpressureConfig,
    BackpressureSnapshot,
    evaluate_audio_backpressure,
)
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
    "AudioBackpressureDiagnostic",
    "BackpressureConfig",
    "BackpressureSnapshot",
    "DEFAULT_BACKPRESSURE_CONFIG",
    "DEFAULT_SUSTAINED_BACKLOG_THRESHOLD_SECONDS",
    "DEFAULT_VAD_CHUNKING_CONFIG",
    "FILE_INPUT_BACKPRESSURE_RECOMMENDATION",
    "FileAudioSource",
    "InvalidVadTimestampError",
    "InvalidWavFileError",
    "SileroVadDetector",
    "SpeechWindow",
    "SttChunkWindow",
    "VadChunkingConfig",
    "aggregate_speech_windows",
    "detect_speech_windows",
    "evaluate_audio_backpressure",
    "speech_windows_from_timestamps",
]
