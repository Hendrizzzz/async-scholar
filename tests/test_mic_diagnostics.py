from __future__ import annotations

import asyncio
import subprocess
import sys
from collections.abc import AsyncIterator, Sequence

import pytest

from async_scholar.audio import (
    DeterministicFakeMicrophoneSource,
    MicrophoneCaptureConfig,
    MicrophoneDiagnosticSummary,
    collect_microphone_diagnostics,
)


class _TinyChunk:
    def __init__(
        self,
        *,
        start_seconds: float,
        end_seconds: float,
        sample_rate_hz: int = 16_000,
        channel_count: int = 1,
    ) -> None:
        self.start_seconds = start_seconds
        self.end_seconds = end_seconds
        self.sample_rate_hz = sample_rate_hz
        self.channel_count = channel_count
        self.pcm_bytes = b"private chunk bytes"


class _ChunkMissingChannelCount:
    start_seconds = 0.0
    end_seconds = 1.0
    sample_rate_hz = 16_000
    pcm_bytes = b"private chunk bytes"


class _TinyMicrophoneSource:
    config = MicrophoneCaptureConfig()

    def __init__(self, chunks: Sequence[object]) -> None:
        self._chunks = chunks

    def __aiter__(self) -> AsyncIterator[object]:
        return self._iter_chunks()

    async def _iter_chunks(self) -> AsyncIterator[object]:
        for chunk in self._chunks:
            yield chunk


def test_microphone_diagnostics_empty_source_returns_zero_summary() -> None:
    source = DeterministicFakeMicrophoneSource(pcm_payloads=[])

    summary = asyncio.run(collect_microphone_diagnostics(source))

    assert summary == MicrophoneDiagnosticSummary(
        chunk_count=0,
        total_audio_seconds=0.0,
        first_start_seconds=None,
        last_end_seconds=None,
        sample_rate_hz=None,
        channel_count=None,
        continuity_count=0,
        gap_count=0,
        overlap_count=0,
    )


def test_microphone_diagnostics_counts_contiguous_fake_chunks() -> None:
    private_payload = b"private raw microphone diagnostic bytes"
    source = DeterministicFakeMicrophoneSource(
        pcm_payloads=[private_payload, b"second", b"third"],
        config=MicrophoneCaptureConfig(
            sample_rate_hz=8_000,
            channel_count=2,
            chunk_duration_seconds=0.25,
        ),
    )

    summary = asyncio.run(collect_microphone_diagnostics(source))

    assert summary.chunk_count == 3
    assert summary.total_audio_seconds == pytest.approx(0.75)
    assert summary.first_start_seconds == 0.0
    assert summary.last_end_seconds == 0.75
    assert summary.sample_rate_hz == 8_000
    assert summary.channel_count == 2
    assert summary.continuity_count == 2
    assert summary.gap_count == 0
    assert summary.overlap_count == 0
    assert "private raw microphone diagnostic bytes" not in repr(summary)
    assert not any(isinstance(value, bytes) for value in vars(summary).values())


def test_microphone_diagnostics_counts_gaps_and_overlaps() -> None:
    source = _TinyMicrophoneSource(
        [
            _TinyChunk(start_seconds=0.0, end_seconds=1.0),
            _TinyChunk(start_seconds=1.25, end_seconds=2.0),
            _TinyChunk(start_seconds=1.75, end_seconds=2.5),
        ],
    )

    summary = asyncio.run(collect_microphone_diagnostics(source))

    assert summary.chunk_count == 3
    assert summary.total_audio_seconds == pytest.approx(2.5)
    assert summary.first_start_seconds == 0.0
    assert summary.last_end_seconds == 2.5
    assert summary.continuity_count == 0
    assert summary.gap_count == 1
    assert summary.overlap_count == 1


@pytest.mark.parametrize(
    ("chunks", "match"),
    [
        (
            [_TinyChunk(start_seconds=float("nan"), end_seconds=1.0)],
            r"chunk 0 start_seconds must be finite and non-negative",
        ),
        (
            [_TinyChunk(start_seconds=-0.01, end_seconds=1.0)],
            r"chunk 0 start_seconds must be finite and non-negative",
        ),
        (
            [_TinyChunk(start_seconds=1.0, end_seconds=0.5)],
            r"chunk 0 end_seconds must be greater than or equal to start_seconds",
        ),
        (
            [
                _TinyChunk(start_seconds=1.0, end_seconds=2.0),
                _TinyChunk(start_seconds=0.5, end_seconds=2.5),
            ],
            r"chunk 1 start_seconds must not move backward",
        ),
        (
            [
                _TinyChunk(start_seconds=0.0, end_seconds=2.0),
                _TinyChunk(start_seconds=1.5, end_seconds=1.75),
            ],
            r"chunk 1 end_seconds must not move backward",
        ),
    ],
)
def test_microphone_diagnostics_rejects_invalid_timing(
    chunks: list[_TinyChunk],
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        asyncio.run(collect_microphone_diagnostics(_TinyMicrophoneSource(chunks)))


@pytest.mark.parametrize(
    ("chunks", "match"),
    [
        (
            [
                _TinyChunk(start_seconds=0.0, end_seconds=1.0),
                _TinyChunk(start_seconds=1.0, end_seconds=2.0, sample_rate_hz=8_000),
            ],
            r"chunk sample_rate_hz must be consistent across source",
        ),
        (
            [
                _TinyChunk(start_seconds=0.0, end_seconds=1.0),
                _TinyChunk(start_seconds=1.0, end_seconds=2.0, channel_count=2),
            ],
            r"chunk channel_count must be consistent across source",
        ),
        (
            [_TinyChunk(start_seconds=0.0, end_seconds=1.0, sample_rate_hz=0)],
            r"chunk 0 sample_rate_hz must be positive",
        ),
        (
            [_TinyChunk(start_seconds=0.0, end_seconds=1.0, channel_count=0)],
            r"chunk 0 channel_count must be positive",
        ),
    ],
)
def test_microphone_diagnostics_rejects_inconsistent_chunk_metadata(
    chunks: list[_TinyChunk],
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        asyncio.run(collect_microphone_diagnostics(_TinyMicrophoneSource(chunks)))


def test_microphone_diagnostics_rejects_missing_chunk_metadata() -> None:
    with pytest.raises(TypeError, match="chunk 0 is missing channel_count"):
        asyncio.run(
            collect_microphone_diagnostics(
                _TinyMicrophoneSource([_ChunkMissingChannelCount()]),
            ),
        )


def test_microphone_diagnostics_summary_validation() -> None:
    with pytest.raises(
        ValueError,
        match="continuity_count, gap_count, and overlap_count must sum",
    ):
        MicrophoneDiagnosticSummary(
            chunk_count=2,
            total_audio_seconds=1.0,
            first_start_seconds=0.0,
            last_end_seconds=1.0,
            sample_rate_hz=16_000,
            channel_count=1,
            continuity_count=0,
            gap_count=0,
            overlap_count=0,
        )


def test_mic_diagnostics_imports_do_not_load_hardware_or_model_dependencies() -> None:
    code = """
import sys

import async_scholar.audio
import async_scholar.audio.mic_diagnostics

banned = {
    "faster_whisper",
    "pyaudio",
    "silero_vad",
    "soundcard",
    "sounddevice",
    "torch",
    "torchaudio",
}
loaded = sorted(name for name in banned if name in sys.modules)
if loaded:
    raise SystemExit(f"unexpected eager imports: {loaded}")
"""

    subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )
