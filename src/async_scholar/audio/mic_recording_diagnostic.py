"""Bounded microphone WAV recording diagnostic."""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import re
import wave
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from async_scholar.audio.level_meter import measure_microphone_level
from async_scholar.audio.mic_signal_diagnostics import (
    DEFAULT_MIC_SIGNAL_DIAGNOSTIC_CONFIG,
    MicrophoneSignalDiagnosticConfig,
    diagnose_microphone_signal,
)
from async_scholar.audio.mic_source import (
    DEFAULT_MIC_CAPTURE_CONFIG,
    MicrophoneCaptureConfig,
    MicrophonePcmChunk,
    MicrophoneSource,
)

DEFAULT_MIC_RECORDING_DIAGNOSTIC_WAV_FILENAME = "microphone.wav"
DEFAULT_MIC_RECORDING_DIAGNOSTIC_REPORT_FILENAME = "diagnostic-report.json"
MIC_RECORDING_DIAGNOSTIC_DIRECTORY_PREFIX = "audio-diagnostic-"

_PCM_SAMPLE_WIDTH_BYTES = 2
_TIMESTAMP_PATTERN = re.compile(r"\A[A-Za-z0-9_.-]+\Z")


class InvalidMicrophoneRecordingDiagnosticConfigError(ValueError):
    """Raised when a microphone recording diagnostic is not safely bounded."""


@dataclass(frozen=True)
class MicrophoneRecordingDiagnosticReport:
    """Privacy-safe scalar report for one bounded microphone recording."""

    chunk_count: int
    total_audio_seconds: float
    sample_rate_hz: int
    channel_count: int
    peak_level: float
    average_rms_level: float
    silence_detected: bool
    clipping_detected: bool
    wav_filename: str = DEFAULT_MIC_RECORDING_DIAGNOSTIC_WAV_FILENAME
    report_filename: str = DEFAULT_MIC_RECORDING_DIAGNOSTIC_REPORT_FILENAME

    def to_json_dict(self) -> dict[str, object]:
        """Return only privacy-safe JSON report fields."""
        return {
            "artifact_filenames": {
                "report": self.report_filename,
                "wav": self.wav_filename,
            },
            "average_rms_level": self.average_rms_level,
            "channel_count": self.channel_count,
            "chunk_count": self.chunk_count,
            "clipping_detected": self.clipping_detected,
            "peak_level": self.peak_level,
            "sample_rate_hz": self.sample_rate_hz,
            "silence_detected": self.silence_detected,
            "total_audio_seconds": self.total_audio_seconds,
        }


@dataclass(frozen=True)
class MicrophoneRecordingDiagnosticResult:
    """Filesystem result for a bounded microphone recording diagnostic."""

    artifact_dir: Path
    wav_path: Path
    report_path: Path
    report: MicrophoneRecordingDiagnosticReport


async def record_microphone_diagnostic(
    source: MicrophoneSource,
    output_root: str | Path,
    *,
    seconds: float,
    max_chunks: int,
    timestamp: str | None = None,
    signal_config: MicrophoneSignalDiagnosticConfig | None = None,
) -> MicrophoneRecordingDiagnosticResult:
    """Record bounded microphone chunks to WAV and write a scalar report."""
    _validate_bounds(seconds=seconds, max_chunks=max_chunks)

    config = source.config
    _validate_capture_config(config)

    timestamp_value = timestamp or _utc_timestamp()
    _validate_timestamp(timestamp_value)

    artifact_dir = (
        Path(output_root)
        / f"{MIC_RECORDING_DIAGNOSTIC_DIRECTORY_PREFIX}{timestamp_value}"
    )
    artifact_dir.mkdir(parents=True, exist_ok=False)

    wav_path = artifact_dir / DEFAULT_MIC_RECORDING_DIAGNOSTIC_WAV_FILENAME
    report_path = artifact_dir / DEFAULT_MIC_RECORDING_DIAGNOSTIC_REPORT_FILENAME

    max_frames = max(1, math.ceil(seconds * config.sample_rate_hz))
    frames_written = 0
    chunks_seen = 0
    readings = []

    with wave.open(str(wav_path), "wb") as wav_file:
        wav_file.setnchannels(config.channel_count)
        wav_file.setsampwidth(_PCM_SAMPLE_WIDTH_BYTES)
        wav_file.setframerate(config.sample_rate_hz)

        chunk_iterator = aiter(source)
        try:
            while chunks_seen < max_chunks and frames_written < max_frames:
                try:
                    chunk = await anext(chunk_iterator)
                except StopAsyncIteration:
                    break

                chunks_seen += 1
                _validate_chunk_format(chunk, config)
                chunk_frame_count = _frame_count(chunk.pcm_bytes, config.channel_count)
                if chunk_frame_count == 0:
                    continue

                remaining_frames = max_frames - frames_written
                frames_to_write = min(chunk_frame_count, remaining_frames)
                if frames_to_write <= 0:
                    break

                trimmed_chunk = _trim_chunk(
                    chunk,
                    config=config,
                    start_frame=frames_written,
                    frames_to_write=frames_to_write,
                )
                wav_file.writeframes(trimmed_chunk.pcm_bytes)
                readings.append(measure_microphone_level(trimmed_chunk))
                frames_written += frames_to_write
        finally:
            close_iterator = getattr(chunk_iterator, "aclose", None)
            if close_iterator is not None:
                await close_iterator()

    signal_summary = diagnose_microphone_signal(
        readings,
        config=signal_config or DEFAULT_MIC_SIGNAL_DIAGNOSTIC_CONFIG,
    )
    report = MicrophoneRecordingDiagnosticReport(
        chunk_count=len(readings),
        total_audio_seconds=frames_written / config.sample_rate_hz,
        sample_rate_hz=config.sample_rate_hz,
        channel_count=config.channel_count,
        peak_level=signal_summary.peak_level,
        average_rms_level=signal_summary.average_rms_level,
        silence_detected=signal_summary.silence_detected,
        clipping_detected=signal_summary.clipping_detected,
    )

    report_path.write_text(
        format_microphone_recording_diagnostic_report(report),
        encoding="utf-8",
    )

    return MicrophoneRecordingDiagnosticResult(
        artifact_dir=artifact_dir,
        wav_path=wav_path,
        report_path=report_path,
        report=report,
    )


def format_microphone_recording_diagnostic_report(
    report: MicrophoneRecordingDiagnosticReport,
) -> str:
    """Format a microphone recording diagnostic report as stable JSON."""
    return json.dumps(report.to_json_dict(), indent=2, sort_keys=True) + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write a bounded local microphone WAV diagnostic artifact.",
    )
    parser.add_argument(
        "--output-root",
        required=True,
        help="Explicit output root for the audio-diagnostic timestamp directory.",
    )
    parser.add_argument(
        "--seconds",
        required=True,
        type=float,
        help="Maximum audio seconds to write.",
    )
    parser.add_argument(
        "--max-chunks",
        required=True,
        type=int,
        help="Maximum microphone chunks to consume.",
    )
    parser.add_argument(
        "--device-id",
        default=None,
        help="Optional microphone device identifier for the sounddevice source.",
    )
    return parser


async def run_microphone_recording_diagnostic(
    *,
    output_root: str | Path,
    seconds: float,
    max_chunks: int,
    device_id: str | None = None,
    source_factory: Callable[
        [MicrophoneCaptureConfig, str | None, int],
        MicrophoneSource,
    ]
    | None = None,
    timestamp: str | None = None,
) -> MicrophoneRecordingDiagnosticResult:
    """Build a source lazily and run the bounded recording diagnostic."""
    config = DEFAULT_MIC_CAPTURE_CONFIG
    source_builder = source_factory or _build_sounddevice_microphone_source
    source = source_builder(config, device_id, max_chunks)
    return await record_microphone_diagnostic(
        source,
        output_root,
        seconds=seconds,
        max_chunks=max_chunks,
        timestamp=timestamp,
    )


def main(
    argv: Sequence[str] | None = None,
    *,
    source_factory: Callable[
        [MicrophoneCaptureConfig, str | None, int],
        MicrophoneSource,
    ]
    | None = None,
    timestamp_factory: Callable[[], str] | None = None,
) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    timestamp = timestamp_factory() if timestamp_factory is not None else None
    result = asyncio.run(
        run_microphone_recording_diagnostic(
            output_root=args.output_root,
            seconds=args.seconds,
            max_chunks=args.max_chunks,
            device_id=args.device_id,
            source_factory=source_factory,
            timestamp=timestamp,
        ),
    )
    print(format_microphone_recording_diagnostic_report(result.report), end="")
    return 0


def _build_sounddevice_microphone_source(
    config: MicrophoneCaptureConfig,
    device_id: str | None,
    max_chunks: int,
) -> MicrophoneSource:
    from async_scholar.audio.sounddevice_mic_source import SoundDeviceMicrophoneSource

    return SoundDeviceMicrophoneSource(
        config=config,
        device_id=device_id,
        max_chunks=max_chunks,
    )


def _utc_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _validate_bounds(*, seconds: float, max_chunks: int) -> None:
    if not math.isfinite(seconds) or seconds <= 0:
        raise InvalidMicrophoneRecordingDiagnosticConfigError(
            "seconds must be a finite value greater than zero",
        )
    if (
        isinstance(max_chunks, bool)
        or not isinstance(max_chunks, int)
        or max_chunks <= 0
    ):
        raise InvalidMicrophoneRecordingDiagnosticConfigError(
            "max_chunks must be a positive integer",
        )


def _validate_capture_config(config: MicrophoneCaptureConfig) -> None:
    if config.sample_rate_hz <= 0:
        raise InvalidMicrophoneRecordingDiagnosticConfigError(
            "sample_rate_hz must be greater than zero",
        )
    if config.channel_count <= 0:
        raise InvalidMicrophoneRecordingDiagnosticConfigError(
            "channel_count must be greater than zero",
        )


def _validate_timestamp(timestamp: str) -> None:
    if not timestamp or _TIMESTAMP_PATTERN.fullmatch(timestamp) is None:
        raise InvalidMicrophoneRecordingDiagnosticConfigError(
            "timestamp must contain only letters, numbers, dots, dashes, or "
            "underscores",
        )


def _validate_chunk_format(
    chunk: MicrophonePcmChunk,
    config: MicrophoneCaptureConfig,
) -> None:
    if chunk.sample_rate_hz != config.sample_rate_hz:
        raise InvalidMicrophoneRecordingDiagnosticConfigError(
            "chunk sample_rate_hz must match capture config",
        )
    if chunk.channel_count != config.channel_count:
        raise InvalidMicrophoneRecordingDiagnosticConfigError(
            "chunk channel_count must match capture config",
        )
    _frame_count(chunk.pcm_bytes, config.channel_count)


def _frame_count(pcm_bytes: bytes, channel_count: int) -> int:
    bytes_per_frame = channel_count * _PCM_SAMPLE_WIDTH_BYTES
    if len(pcm_bytes) % bytes_per_frame != 0:
        raise InvalidMicrophoneRecordingDiagnosticConfigError(
            "PCM chunk byte length must align to signed 16-bit frames",
        )
    return len(pcm_bytes) // bytes_per_frame


def _trim_chunk(
    chunk: MicrophonePcmChunk,
    *,
    config: MicrophoneCaptureConfig,
    start_frame: int,
    frames_to_write: int,
) -> MicrophonePcmChunk:
    bytes_to_write = frames_to_write * config.channel_count * _PCM_SAMPLE_WIDTH_BYTES
    start_seconds = start_frame / config.sample_rate_hz
    end_seconds = (start_frame + frames_to_write) / config.sample_rate_hz
    return MicrophonePcmChunk(
        start_seconds=start_seconds,
        end_seconds=end_seconds,
        pcm_bytes=chunk.pcm_bytes[:bytes_to_write],
        sample_rate_hz=config.sample_rate_hz,
        channel_count=config.channel_count,
    )


if __name__ == "__main__":
    raise SystemExit(main())
