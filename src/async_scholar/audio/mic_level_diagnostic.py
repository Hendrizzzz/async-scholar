"""Bounded live microphone level diagnostics."""

from __future__ import annotations

import argparse
import asyncio
import inspect
import json
import math
import sys
import time
from collections.abc import AsyncIterator, Callable, Sequence
from dataclasses import asdict, dataclass
from typing import Protocol, TextIO

from async_scholar.audio.level_meter import measure_microphone_level
from async_scholar.audio.mic_signal_diagnostics import (
    DEFAULT_MIC_SIGNAL_CLIPPING_THRESHOLD,
    DEFAULT_MIC_SIGNAL_SILENCE_THRESHOLD,
    InvalidMicrophoneSignalDiagnosticConfigError,
    MicrophoneSignalDiagnosticConfig,
    diagnose_microphone_signal,
)
from async_scholar.audio.mic_source import (
    DEFAULT_MIC_CHANNEL_COUNT,
    DEFAULT_MIC_SAMPLE_RATE_HZ,
    MicrophoneCaptureConfig,
    MicrophonePcmChunk,
)

DEFAULT_MIC_LEVEL_DIAGNOSTIC_SECONDS = 3.0
DEFAULT_MIC_LEVEL_DIAGNOSTIC_MAX_CHUNKS = 3
_SOUNDDEVICE_DEVICE_ID_PREFIX = "sounddevice:"


class InvalidMicrophoneLevelDiagnosticConfigError(ValueError):
    """Raised when microphone level diagnostic bounds are invalid."""


class _MicrophoneLevelSource(Protocol):
    """Small source shape needed by this diagnostic."""

    config: MicrophoneCaptureConfig

    def _iter_chunks(self) -> AsyncIterator[MicrophonePcmChunk]:
        """Yield live PCM chunks."""


@dataclass(frozen=True)
class MicrophoneLevelDiagnosticReport:
    """Privacy-safe scalar summary of a bounded microphone level check."""

    requested_duration_seconds: float
    requested_max_chunks: int
    chunk_count: int
    total_audio_seconds: float
    peak_level: float
    average_rms_level: float
    silence_threshold: float
    clipping_threshold: float
    silent_reading_count: int
    clipped_reading_count: int
    silence_detected: bool
    clipping_detected: bool
    sample_rate_hz: int
    channel_count: int
    any_chunks_observed: bool

    def to_privacy_safe_dict(self) -> dict[str, int | float | bool]:
        """Return report metadata without source objects or raw audio."""

        return asdict(self)


MicrophoneLevelSourceFactory = Callable[
    [MicrophoneCaptureConfig, str | None, int], _MicrophoneLevelSource
]


def _validate_seconds(seconds: float) -> float:
    try:
        normalized_seconds = float(seconds)
    except (TypeError, ValueError) as exc:
        raise InvalidMicrophoneLevelDiagnosticConfigError(
            "seconds must be a finite positive number"
        ) from exc
    if not math.isfinite(normalized_seconds) or normalized_seconds <= 0.0:
        raise InvalidMicrophoneLevelDiagnosticConfigError(
            "seconds must be a finite positive number"
        )
    return normalized_seconds


def _validate_max_chunks(max_chunks: int) -> int:
    if isinstance(max_chunks, bool):
        raise InvalidMicrophoneLevelDiagnosticConfigError(
            "max_chunks must be a positive integer"
        )
    try:
        normalized_max_chunks = int(max_chunks)
    except (TypeError, ValueError) as exc:
        raise InvalidMicrophoneLevelDiagnosticConfigError(
            "max_chunks must be a positive integer"
        ) from exc
    if normalized_max_chunks <= 0:
        raise InvalidMicrophoneLevelDiagnosticConfigError(
            "max_chunks must be a positive integer"
        )
    return normalized_max_chunks


def _validate_device_id(device_id: str | None) -> str | None:
    if device_id is None:
        return None
    if not isinstance(device_id, str):
        raise InvalidMicrophoneLevelDiagnosticConfigError(
            "device_id must use sounddevice:<index>"
        )
    if not device_id.startswith(_SOUNDDEVICE_DEVICE_ID_PREFIX):
        raise InvalidMicrophoneLevelDiagnosticConfigError(
            "device_id must use sounddevice:<index>"
        )
    index_text = device_id.removeprefix(_SOUNDDEVICE_DEVICE_ID_PREFIX)
    if not index_text or not index_text.isdecimal():
        raise InvalidMicrophoneLevelDiagnosticConfigError(
            "device_id must use sounddevice:<index>"
        )
    return device_id


def _validate_signal_diagnostic_config(
    *,
    silence_threshold: float,
    clipping_threshold: float,
) -> MicrophoneSignalDiagnosticConfig:
    try:
        return MicrophoneSignalDiagnosticConfig(
            silence_threshold=silence_threshold,
            clipping_threshold=clipping_threshold,
        )
    except InvalidMicrophoneSignalDiagnosticConfigError as exc:
        raise InvalidMicrophoneLevelDiagnosticConfigError(str(exc)) from exc


def _default_source_factory(
    config: MicrophoneCaptureConfig,
    device_id: str | None,
    max_chunks: int,
) -> _MicrophoneLevelSource:
    from async_scholar.audio.sounddevice_mic_source import SoundDeviceMicrophoneSource

    return SoundDeviceMicrophoneSource(
        config=config,
        device_id=device_id,
        max_chunks=max_chunks,
    )


def _source_sample_rate_hz(source: _MicrophoneLevelSource) -> int:
    config = getattr(source, "config", None)
    return int(getattr(config, "sample_rate_hz", DEFAULT_MIC_SAMPLE_RATE_HZ))


def _source_channel_count(source: _MicrophoneLevelSource) -> int:
    config = getattr(source, "config", None)
    return int(getattr(config, "channel_count", DEFAULT_MIC_CHANNEL_COUNT))


async def collect_microphone_level_diagnostic(
    source: _MicrophoneLevelSource,
    *,
    seconds: float = DEFAULT_MIC_LEVEL_DIAGNOSTIC_SECONDS,
    max_chunks: int = DEFAULT_MIC_LEVEL_DIAGNOSTIC_MAX_CHUNKS,
    silence_threshold: float = DEFAULT_MIC_SIGNAL_SILENCE_THRESHOLD,
    clipping_threshold: float = DEFAULT_MIC_SIGNAL_CLIPPING_THRESHOLD,
) -> MicrophoneLevelDiagnosticReport:
    """Collect bounded level readings from an already-created microphone source."""

    requested_duration_seconds = _validate_seconds(seconds)
    requested_max_chunks = _validate_max_chunks(max_chunks)
    signal_config = _validate_signal_diagnostic_config(
        silence_threshold=silence_threshold,
        clipping_threshold=clipping_threshold,
    )

    chunk_count = 0
    total_audio_seconds = 0.0
    sample_rate_hz = _source_sample_rate_hz(source)
    channel_count = _source_channel_count(source)
    started_at = time.monotonic()
    chunks = source._iter_chunks()
    readings = []

    try:
        while (
            chunk_count < requested_max_chunks
            and total_audio_seconds < requested_duration_seconds
        ):
            remaining_wall_seconds = requested_duration_seconds - (
                time.monotonic() - started_at
            )
            if remaining_wall_seconds <= 0.0:
                break
            try:
                chunk = await asyncio.wait_for(
                    chunks.__anext__(),
                    timeout=remaining_wall_seconds,
                )
            except (StopAsyncIteration, TimeoutError):
                break

            reading = measure_microphone_level(chunk)
            chunk_count += 1
            readings.append(reading)
            total_audio_seconds += max(0.0, reading.end_seconds - reading.start_seconds)
            sample_rate_hz = reading.sample_rate_hz
            channel_count = reading.channel_count
    finally:
        aclose = getattr(chunks, "aclose", None)
        if callable(aclose):
            await aclose()

    signal_summary = diagnose_microphone_signal(readings, config=signal_config)

    return MicrophoneLevelDiagnosticReport(
        requested_duration_seconds=requested_duration_seconds,
        requested_max_chunks=requested_max_chunks,
        chunk_count=chunk_count,
        total_audio_seconds=total_audio_seconds,
        peak_level=signal_summary.peak_level,
        average_rms_level=signal_summary.average_rms_level,
        silence_threshold=signal_config.silence_threshold,
        clipping_threshold=signal_config.clipping_threshold,
        silent_reading_count=signal_summary.silent_reading_count,
        clipped_reading_count=signal_summary.clipped_reading_count,
        silence_detected=signal_summary.silence_detected,
        clipping_detected=signal_summary.clipping_detected,
        sample_rate_hz=sample_rate_hz,
        channel_count=channel_count,
        any_chunks_observed=chunk_count > 0,
    )


async def _stop_source(source: _MicrophoneLevelSource) -> None:
    stop = getattr(source, "stop", None)
    if not callable(stop):
        return
    stop_result = stop()
    if inspect.isawaitable(stop_result):
        await stop_result


async def run_microphone_level_diagnostic(
    *,
    seconds: float = DEFAULT_MIC_LEVEL_DIAGNOSTIC_SECONDS,
    max_chunks: int = DEFAULT_MIC_LEVEL_DIAGNOSTIC_MAX_CHUNKS,
    silence_threshold: float = DEFAULT_MIC_SIGNAL_SILENCE_THRESHOLD,
    clipping_threshold: float = DEFAULT_MIC_SIGNAL_CLIPPING_THRESHOLD,
    device_id: str | None = None,
    source_factory: MicrophoneLevelSourceFactory | None = None,
) -> MicrophoneLevelDiagnosticReport:
    """Create a live microphone source and collect a bounded level summary."""

    requested_duration_seconds = _validate_seconds(seconds)
    requested_max_chunks = _validate_max_chunks(max_chunks)
    validated_device_id = _validate_device_id(device_id)
    signal_config = _validate_signal_diagnostic_config(
        silence_threshold=silence_threshold,
        clipping_threshold=clipping_threshold,
    )
    config = MicrophoneCaptureConfig()
    factory = source_factory or _default_source_factory
    source = factory(config, validated_device_id, requested_max_chunks)
    try:
        return await collect_microphone_level_diagnostic(
            source,
            seconds=requested_duration_seconds,
            max_chunks=requested_max_chunks,
            silence_threshold=signal_config.silence_threshold,
            clipping_threshold=signal_config.clipping_threshold,
        )
    finally:
        await _stop_source(source)


def format_microphone_level_diagnostic_report(
    report: MicrophoneLevelDiagnosticReport,
) -> str:
    """Format a privacy-safe report for console output."""

    return json.dumps(report.to_privacy_safe_dict(), indent=2, sort_keys=True)


def _parse_seconds(raw_seconds: str) -> float:
    try:
        return _validate_seconds(float(raw_seconds))
    except InvalidMicrophoneLevelDiagnosticConfigError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _parse_max_chunks(raw_max_chunks: str) -> int:
    try:
        if not raw_max_chunks.isdecimal():
            raise InvalidMicrophoneLevelDiagnosticConfigError(
                "max_chunks must be a positive integer"
            )
        return _validate_max_chunks(int(raw_max_chunks))
    except InvalidMicrophoneLevelDiagnosticConfigError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _parse_device_id(raw_device_id: str) -> str:
    try:
        return _validate_device_id(raw_device_id) or raw_device_id
    except InvalidMicrophoneLevelDiagnosticConfigError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _parse_signal_threshold(name: str, raw_threshold: str) -> float:
    try:
        threshold = float(raw_threshold)
        config_kwargs = {
            "silence_threshold": DEFAULT_MIC_SIGNAL_SILENCE_THRESHOLD,
            "clipping_threshold": DEFAULT_MIC_SIGNAL_CLIPPING_THRESHOLD,
            name: threshold,
        }
        config = _validate_signal_diagnostic_config(**config_kwargs)
        return getattr(config, name)
    except (InvalidMicrophoneLevelDiagnosticConfigError, ValueError) as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _parse_silence_threshold(raw_threshold: str) -> float:
    return _parse_signal_threshold("silence_threshold", raw_threshold)


def _parse_clipping_threshold(raw_threshold: str) -> float:
    return _parse_signal_threshold("clipping_threshold", raw_threshold)


def build_parser() -> argparse.ArgumentParser:
    """Build the microphone level diagnostic argument parser."""

    parser = argparse.ArgumentParser(
        description="Run a bounded live microphone level diagnostic.",
    )
    parser.add_argument(
        "--device-id",
        type=_parse_device_id,
        default=None,
        help="Optional live microphone source id in sounddevice:<index> form.",
    )
    parser.add_argument(
        "--seconds",
        type=_parse_seconds,
        default=DEFAULT_MIC_LEVEL_DIAGNOSTIC_SECONDS,
        help="Maximum live capture duration in seconds.",
    )
    parser.add_argument(
        "--max-chunks",
        type=_parse_max_chunks,
        default=DEFAULT_MIC_LEVEL_DIAGNOSTIC_MAX_CHUNKS,
        help="Maximum number of microphone chunks to summarize.",
    )
    parser.add_argument(
        "--silence-threshold",
        type=_parse_silence_threshold,
        default=DEFAULT_MIC_SIGNAL_SILENCE_THRESHOLD,
        help="Normalized RMS level at or below which a reading is silent.",
    )
    parser.add_argument(
        "--clipping-threshold",
        type=_parse_clipping_threshold,
        default=DEFAULT_MIC_SIGNAL_CLIPPING_THRESHOLD,
        help="Normalized peak level at or above which a reading is clipped.",
    )
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    source_factory: MicrophoneLevelSourceFactory | None = None,
    stdout: TextIO | None = None,
) -> int:
    """Run the module command."""

    parser = build_parser()
    args = parser.parse_args(argv)
    report = asyncio.run(
        run_microphone_level_diagnostic(
            seconds=args.seconds,
            max_chunks=args.max_chunks,
            silence_threshold=args.silence_threshold,
            clipping_threshold=args.clipping_threshold,
            device_id=args.device_id,
            source_factory=source_factory,
        )
    )
    print(format_microphone_level_diagnostic_report(report), file=stdout or sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
