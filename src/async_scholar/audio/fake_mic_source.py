"""Deterministic in-memory microphone source for tests and diagnostics."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass, field

from async_scholar.audio.mic_source import (
    MicrophoneCaptureConfig,
    MicrophonePcmChunk,
)


@dataclass(frozen=True)
class DeterministicFakeMicrophoneSource:
    """In-memory ``MicrophoneSource`` implementation with deterministic timing."""

    pcm_payloads: Sequence[bytes] = field(default_factory=tuple, repr=False)
    config: MicrophoneCaptureConfig = field(
        default_factory=MicrophoneCaptureConfig,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.config, MicrophoneCaptureConfig):
            raise TypeError("config must be a MicrophoneCaptureConfig")
        object.__setattr__(
            self,
            "pcm_payloads",
            _validated_payload_tuple(self.pcm_payloads),
        )

    def __aiter__(self) -> AsyncIterator[MicrophonePcmChunk]:
        return self._iter_chunks()

    async def _iter_chunks(self) -> AsyncIterator[MicrophonePcmChunk]:
        duration_seconds = self.config.chunk_duration_seconds
        for index, pcm_payload in enumerate(self.pcm_payloads):
            yield MicrophonePcmChunk(
                start_seconds=index * duration_seconds,
                end_seconds=(index + 1) * duration_seconds,
                pcm_bytes=pcm_payload,
                sample_rate_hz=self.config.sample_rate_hz,
                channel_count=self.config.channel_count,
            )


def _validated_payload_tuple(pcm_payloads: Sequence[bytes]) -> tuple[bytes, ...]:
    if isinstance(pcm_payloads, bytes | bytearray | memoryview | str):
        raise TypeError("pcm_payloads must be a sequence of bytes payloads")
    if not isinstance(pcm_payloads, Sequence):
        raise TypeError("pcm_payloads must be a sequence of bytes payloads")

    payload_tuple = tuple(pcm_payloads)
    for index, pcm_payload in enumerate(payload_tuple):
        if not isinstance(pcm_payload, bytes):
            raise TypeError(f"pcm_payloads[{index}] must be bytes")
    return payload_tuple


__all__ = ["DeterministicFakeMicrophoneSource"]
