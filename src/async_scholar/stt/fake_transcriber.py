"""Deterministic fake transcriber for WAV pipeline tests."""

from dataclasses import dataclass
from hashlib import sha256

from async_scholar.audio import FileAudioSource
from async_scholar.schemas import TranscriptSegment
from async_scholar.stt.transcriber import AudioInput


@dataclass(frozen=True)
class _ChunkRecord:
    start_seconds: float
    end_seconds: float
    pcm_bytes: bytes


@dataclass(frozen=True)
class DeterministicFakeTranscriber:
    """Create stable transcript segments from WAV chunk boundaries."""

    chunk_duration_seconds: float = 5.0

    def __post_init__(self) -> None:
        if self.chunk_duration_seconds <= 0:
            msg = "chunk_duration_seconds must be greater than 0"
            raise ValueError(msg)

    def transcribe(self, source: AudioInput) -> list[TranscriptSegment]:
        audio_source = self._coerce_source(source)
        chunks = [
            _ChunkRecord(
                start_seconds=chunk.start_seconds,
                end_seconds=chunk.end_seconds,
                pcm_bytes=chunk.pcm_bytes,
            )
            for chunk in audio_source.iter_chunks(self.chunk_duration_seconds)
        ]

        if not chunks:
            return []

        session_id = self._session_id(audio_source, chunks)
        segment_count = len(chunks)
        return [
            TranscriptSegment(
                segment_id=f"{session_id}-segment-{index + 1:04d}",
                session_id=session_id,
                start_seconds=chunk.start_seconds,
                end_seconds=chunk.end_seconds,
                text=(
                    "Deterministic fake transcript "
                    f"segment {index + 1} of {segment_count}."
                ),
            )
            for index, chunk in enumerate(chunks)
        ]

    def _coerce_source(self, source: AudioInput) -> FileAudioSource:
        if isinstance(source, FileAudioSource):
            return source
        return FileAudioSource(source)

    def _session_id(
        self,
        source: FileAudioSource,
        chunks: list[_ChunkRecord],
    ) -> str:
        metadata = source.metadata
        digest = sha256()
        digest.update(str(metadata.sample_rate).encode("ascii"))
        digest.update(str(metadata.channel_count).encode("ascii"))
        digest.update(str(metadata.sample_width_bytes).encode("ascii"))
        digest.update(str(metadata.frame_count).encode("ascii"))
        digest.update(str(self.chunk_duration_seconds).encode("ascii"))

        for chunk in chunks:
            digest.update(str(chunk.start_seconds).encode("ascii"))
            digest.update(str(chunk.end_seconds).encode("ascii"))
            digest.update(chunk.pcm_bytes)

        return f"fake-stt-{digest.hexdigest()[:12]}"
