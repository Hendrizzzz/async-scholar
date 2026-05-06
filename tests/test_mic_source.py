from __future__ import annotations

import asyncio
import subprocess
import sys
from collections.abc import AsyncIterator

import pytest

from async_scholar.audio import (
    DEFAULT_MIC_CAPTURE_CONFIG,
    DEFAULT_MIC_CHANNEL_COUNT,
    DEFAULT_MIC_CHUNK_DURATION_SECONDS,
    DEFAULT_MIC_SAMPLE_RATE_HZ,
    MicrophoneCaptureConfig,
    MicrophonePcmChunk,
    MicrophoneSource,
)


def test_default_microphone_capture_config_is_conservative() -> None:
    config = MicrophoneCaptureConfig()

    assert config == DEFAULT_MIC_CAPTURE_CONFIG
    assert config.sample_rate_hz == DEFAULT_MIC_SAMPLE_RATE_HZ == 16_000
    assert config.channel_count == DEFAULT_MIC_CHANNEL_COUNT == 1
    assert config.chunk_duration_seconds == DEFAULT_MIC_CHUNK_DURATION_SECONDS == 1.0


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"sample_rate_hz": 0}, "sample_rate_hz must be positive"),
        ({"sample_rate_hz": -16_000}, "sample_rate_hz must be positive"),
        ({"channel_count": 0}, "channel_count must be positive"),
        ({"channel_count": -1}, "channel_count must be positive"),
        (
            {"chunk_duration_seconds": 0.0},
            "chunk_duration_seconds must be finite and positive",
        ),
        (
            {"chunk_duration_seconds": float("inf")},
            "chunk_duration_seconds must be finite and positive",
        ),
        (
            {"chunk_duration_seconds": float("nan")},
            "chunk_duration_seconds must be finite and positive",
        ),
    ],
)
def test_microphone_capture_config_rejects_invalid_values(
    kwargs: dict[str, object],
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        MicrophoneCaptureConfig(**kwargs)


def test_microphone_pcm_chunk_keeps_valid_metadata_and_private_payload() -> None:
    chunk = MicrophonePcmChunk(
        start_seconds=2,
        end_seconds=3.25,
        pcm_bytes=b"private raw pcm",
    )

    assert chunk.start_seconds == 2.0
    assert chunk.end_seconds == 3.25
    assert chunk.duration_seconds == 1.25
    assert chunk.sample_rate_hz == 16_000
    assert chunk.channel_count == 1
    assert chunk.pcm_bytes == b"private raw pcm"
    assert "private raw pcm" not in repr(chunk)
    assert "pcm_bytes" not in repr(chunk)


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        (
            {"start_seconds": -0.01, "end_seconds": 1.0},
            "start_seconds must be finite and non-negative",
        ),
        (
            {"start_seconds": float("inf"), "end_seconds": 1.0},
            "start_seconds must be finite and non-negative",
        ),
        (
            {"start_seconds": 0.0, "end_seconds": -0.01},
            "end_seconds must be finite and non-negative",
        ),
        (
            {"start_seconds": 2.0, "end_seconds": 1.0},
            "end_seconds must be greater than or equal to start_seconds",
        ),
    ],
)
def test_microphone_pcm_chunk_rejects_invalid_timing(
    kwargs: dict[str, object],
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        MicrophonePcmChunk(pcm_bytes=b"", **kwargs)


def test_microphone_source_protocol_shape_with_fake_source() -> None:
    chunk = MicrophonePcmChunk(
        start_seconds=0.0,
        end_seconds=0.5,
        pcm_bytes=b"\x00\x01",
    )
    source: MicrophoneSource = _FakeMicrophoneSource(
        config=MicrophoneCaptureConfig(chunk_duration_seconds=0.5),
        chunks=[chunk],
    )

    assert isinstance(source, MicrophoneSource)
    assert source.config.chunk_duration_seconds == 0.5
    assert asyncio.run(_collect_chunks(source)) == [chunk]


def test_audio_imports_do_not_load_hardware_or_model_dependencies() -> None:
    code = """
import sys

import async_scholar.audio
import async_scholar.audio.mic_source

banned = {
    "faster_whisper",
    "pyaudio",
    "silero_vad",
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


class _FakeMicrophoneSource:
    def __init__(
        self,
        *,
        config: MicrophoneCaptureConfig,
        chunks: list[MicrophonePcmChunk],
    ) -> None:
        self.config = config
        self._chunks = chunks

    def __aiter__(self) -> AsyncIterator[MicrophonePcmChunk]:
        return self._iter_chunks()

    async def _iter_chunks(self) -> AsyncIterator[MicrophonePcmChunk]:
        for chunk in self._chunks:
            yield chunk


async def _collect_chunks(source: MicrophoneSource) -> list[MicrophonePcmChunk]:
    return [chunk async for chunk in source]
