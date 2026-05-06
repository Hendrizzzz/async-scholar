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
from async_scholar.audio.fake_mic_source import DeterministicFakeMicrophoneSource
from async_scholar.audio.file_source import (
    AudioChunk,
    AudioMetadata,
    FileAudioSource,
    InvalidWavFileError,
)
from async_scholar.audio.mic_devices import (
    MicrophoneDeviceMetadata,
    MicrophoneDeviceProvider,
    StaticMicrophoneDeviceProvider,
    validate_microphone_device_listing,
)
from async_scholar.audio.mic_diagnostics import (
    MicrophoneDiagnosticSummary,
    collect_microphone_diagnostics,
)
from async_scholar.audio.mic_source import (
    DEFAULT_MIC_CAPTURE_CONFIG,
    DEFAULT_MIC_CHANNEL_COUNT,
    DEFAULT_MIC_CHUNK_DURATION_SECONDS,
    DEFAULT_MIC_SAMPLE_RATE_HZ,
    MicrophoneCaptureConfig,
    MicrophonePcmChunk,
    MicrophoneSource,
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
    "DEFAULT_MIC_CAPTURE_CONFIG",
    "DEFAULT_MIC_CHANNEL_COUNT",
    "DEFAULT_MIC_CHUNK_DURATION_SECONDS",
    "DEFAULT_MIC_SAMPLE_RATE_HZ",
    "DEFAULT_SUSTAINED_BACKLOG_THRESHOLD_SECONDS",
    "DEFAULT_VAD_CHUNKING_CONFIG",
    "DeterministicFakeMicrophoneSource",
    "FILE_INPUT_BACKPRESSURE_RECOMMENDATION",
    "FileAudioSource",
    "InvalidVadTimestampError",
    "InvalidWavFileError",
    "MicrophoneCaptureConfig",
    "MicrophoneDeviceMetadata",
    "MicrophoneDeviceProvider",
    "MicrophoneDiagnosticSummary",
    "MicrophonePcmChunk",
    "MicrophoneSource",
    "SileroVadDetector",
    "StaticMicrophoneDeviceProvider",
    "SpeechWindow",
    "SttChunkWindow",
    "VadChunkingConfig",
    "aggregate_speech_windows",
    "collect_microphone_diagnostics",
    "detect_speech_windows",
    "evaluate_audio_backpressure",
    "speech_windows_from_timestamps",
    "validate_microphone_device_listing",
]
