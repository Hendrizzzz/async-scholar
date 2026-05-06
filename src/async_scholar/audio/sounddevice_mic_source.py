"""Lazy real microphone capture source backed by sounddevice."""

from __future__ import annotations

import asyncio
import importlib
from collections.abc import AsyncIterator
from types import ModuleType
from typing import Any

from async_scholar.audio.mic_source import (
    DEFAULT_MIC_CAPTURE_CONFIG,
    MicrophoneCaptureConfig,
    MicrophonePcmChunk,
)

SOUNDDEVICE_DEVICE_ID_PREFIX = "sounddevice:"
PCM_SAMPLE_WIDTH_BYTES = 2


class SoundDeviceMicrophoneCaptureError(RuntimeError):
    """Raised when sounddevice cannot return a clean microphone chunk."""


class SoundDeviceMicrophoneSource:
    """A lazy sounddevice-backed source of signed 16-bit PCM microphone chunks."""

    def __init__(
        self,
        *,
        config: MicrophoneCaptureConfig = DEFAULT_MIC_CAPTURE_CONFIG,
        device_id: str | None = None,
        max_chunks: int | None = None,
    ) -> None:
        if not isinstance(config, MicrophoneCaptureConfig):
            raise TypeError("config must be a MicrophoneCaptureConfig")
        self.config = config
        self.device_id = device_id
        self.max_chunks = _validate_max_chunks(max_chunks)
        self._device_index = _parse_sounddevice_device_id(device_id)
        self._stop_requested = False

    def __aiter__(self) -> AsyncIterator[MicrophonePcmChunk]:
        return self._iter_chunks()

    def stop(self) -> None:
        """Request that the async iterator end after the current yielded chunk."""

        self._stop_requested = True

    async def _iter_chunks(self) -> AsyncIterator[MicrophonePcmChunk]:
        if self.max_chunks == 0 or self._stop_requested:
            return

        frames_per_chunk = _frames_per_chunk(self.config)
        sounddevice = _load_sounddevice()
        stream = sounddevice.RawInputStream(
            samplerate=self.config.sample_rate_hz,
            channels=self.config.channel_count,
            dtype="int16",
            blocksize=frames_per_chunk,
            device=self._device_index,
        )

        try:
            stream.start()
            chunk_index = 0
            while not self._stop_requested and (
                self.max_chunks is None or chunk_index < self.max_chunks
            ):
                pcm_bytes = await _read_pcm_bytes(stream, frames_per_chunk)
                start_seconds = chunk_index * self.config.chunk_duration_seconds
                end_seconds = (chunk_index + 1) * self.config.chunk_duration_seconds
                yield MicrophonePcmChunk(
                    start_seconds=start_seconds,
                    end_seconds=end_seconds,
                    sample_rate_hz=self.config.sample_rate_hz,
                    channel_count=self.config.channel_count,
                    pcm_bytes=pcm_bytes,
                )
                chunk_index += 1
        finally:
            _stop_and_close_stream(stream)


def _validate_max_chunks(max_chunks: int | None) -> int | None:
    if max_chunks is None:
        return None
    if not isinstance(max_chunks, int) or isinstance(max_chunks, bool):
        raise TypeError("max_chunks must be a non-negative integer")
    if max_chunks < 0:
        raise ValueError("max_chunks must be a non-negative integer")
    return max_chunks


def _parse_sounddevice_device_id(device_id: str | None) -> int | None:
    if device_id is None:
        return None
    if not isinstance(device_id, str):
        raise TypeError("device_id must use the sounddevice:<index> format")
    if not device_id.startswith(SOUNDDEVICE_DEVICE_ID_PREFIX):
        raise ValueError("device_id must use the sounddevice:<index> format")

    raw_index = device_id.removeprefix(SOUNDDEVICE_DEVICE_ID_PREFIX)
    if not raw_index.isdecimal():
        raise ValueError("device_id must use the sounddevice:<index> format")
    return int(raw_index)


def _frames_per_chunk(config: MicrophoneCaptureConfig) -> int:
    frames = round(config.sample_rate_hz * config.chunk_duration_seconds)
    if frames < 1:
        raise ValueError(
            "chunk_duration_seconds is too short for the configured sample_rate_hz"
        )
    return frames


def _load_sounddevice() -> ModuleType:
    return importlib.import_module("sounddevice")


async def _read_pcm_bytes(stream: Any, frames_per_chunk: int) -> bytes:
    read_result = await asyncio.to_thread(stream.read, frames_per_chunk)
    pcm_data, overflowed = _normalize_sounddevice_read_result(read_result)
    if overflowed:
        raise SoundDeviceMicrophoneCaptureError(
            "sounddevice reported microphone input overflow while reading PCM"
        )
    return bytes(pcm_data)


def _normalize_sounddevice_read_result(read_result: object) -> tuple[object, bool]:
    if isinstance(read_result, tuple):
        if len(read_result) != 2:
            raise SoundDeviceMicrophoneCaptureError(
                "sounddevice RawInputStream.read returned an unexpected tuple"
            )
        pcm_data, overflowed = read_result
        return pcm_data, bool(overflowed)
    return read_result, False


def _stop_and_close_stream(stream: Any) -> None:
    stop = getattr(stream, "stop", None)
    if stop is not None:
        stop()
    close = getattr(stream, "close", None)
    if close is not None:
        close()
