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
from async_scholar.audio.level_meter import (
    InvalidMicrophoneLevelInputError,
    MicrophoneLevelReading,
    collect_microphone_level_readings,
    measure_microphone_level,
)
from async_scholar.audio.mic_device_diagnostics import (
    MicrophoneDeviceDiagnosticSummary,
    collect_microphone_device_diagnostics,
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
from async_scholar.audio.sounddevice_mic_devices import (
    InvalidSoundDeviceMicrophoneMetadataError,
    SoundDeviceMicrophoneDeviceProvider,
)
from async_scholar.audio.sounddevice_mic_source import (
    SoundDeviceMicrophoneCaptureError,
    SoundDeviceMicrophoneSource,
)
from async_scholar.audio.vad import (
    InvalidVadTimestampError,
    SileroVadDetector,
    SpeechWindow,
    detect_speech_windows,
    speech_windows_from_timestamps,
)

_MIC_LEVEL_DIAGNOSTIC_EXPORTS = {
    "DEFAULT_MIC_LEVEL_DIAGNOSTIC_MAX_CHUNKS",
    "DEFAULT_MIC_LEVEL_DIAGNOSTIC_SECONDS",
    "InvalidMicrophoneLevelDiagnosticConfigError",
    "MicrophoneLevelDiagnosticReport",
    "collect_microphone_level_diagnostic",
    "format_microphone_level_diagnostic_report",
    "run_microphone_level_diagnostic",
}


def __getattr__(name: str):
    if name in _MIC_LEVEL_DIAGNOSTIC_EXPORTS:
        from importlib import import_module

        mic_level_diagnostic = import_module("async_scholar.audio.mic_level_diagnostic")
        value = getattr(mic_level_diagnostic, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


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
    "DEFAULT_MIC_LEVEL_DIAGNOSTIC_MAX_CHUNKS",
    "DEFAULT_MIC_LEVEL_DIAGNOSTIC_SECONDS",
    "DEFAULT_MIC_SAMPLE_RATE_HZ",
    "DEFAULT_SUSTAINED_BACKLOG_THRESHOLD_SECONDS",
    "DEFAULT_VAD_CHUNKING_CONFIG",
    "DeterministicFakeMicrophoneSource",
    "FILE_INPUT_BACKPRESSURE_RECOMMENDATION",
    "FileAudioSource",
    "InvalidMicrophoneLevelInputError",
    "InvalidMicrophoneLevelDiagnosticConfigError",
    "InvalidSoundDeviceMicrophoneMetadataError",
    "InvalidVadTimestampError",
    "InvalidWavFileError",
    "MicrophoneCaptureConfig",
    "MicrophoneDeviceDiagnosticSummary",
    "MicrophoneDeviceMetadata",
    "MicrophoneDeviceProvider",
    "MicrophoneDiagnosticSummary",
    "MicrophoneLevelReading",
    "MicrophoneLevelDiagnosticReport",
    "MicrophonePcmChunk",
    "MicrophoneSource",
    "SileroVadDetector",
    "SoundDeviceMicrophoneCaptureError",
    "SoundDeviceMicrophoneDeviceProvider",
    "SoundDeviceMicrophoneSource",
    "StaticMicrophoneDeviceProvider",
    "SpeechWindow",
    "SttChunkWindow",
    "VadChunkingConfig",
    "aggregate_speech_windows",
    "collect_microphone_device_diagnostics",
    "collect_microphone_diagnostics",
    "collect_microphone_level_diagnostic",
    "collect_microphone_level_readings",
    "detect_speech_windows",
    "evaluate_audio_backpressure",
    "format_microphone_level_diagnostic_report",
    "measure_microphone_level",
    "run_microphone_level_diagnostic",
    "speech_windows_from_timestamps",
    "validate_microphone_device_listing",
]
