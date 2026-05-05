"""WAV file chunk reader."""

import wave
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AudioMetadata:
    path: Path
    sample_rate: int
    channel_count: int
    sample_width_bytes: int
    frame_count: int
    duration_seconds: float


@dataclass(frozen=True)
class AudioChunk:
    start_seconds: float
    end_seconds: float
    pcm_bytes: bytes


class InvalidWavFileError(ValueError):
    """Raised when a file cannot be read as a valid WAV file."""


class FileAudioSource:
    """Read deterministic metadata and PCM chunks from a local WAV file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._metadata = self._read_metadata()

    @property
    def metadata(self) -> AudioMetadata:
        return self._metadata

    def iter_chunks(self, chunk_duration_seconds: float) -> Iterator[AudioChunk]:
        frames_per_chunk = self._frames_per_chunk(chunk_duration_seconds)
        bytes_per_frame = self.metadata.channel_count * self.metadata.sample_width_bytes

        try:
            with wave.open(str(self.path), "rb") as wav_file:
                start_frame = 0
                while start_frame < self.metadata.frame_count:
                    pcm_bytes = wav_file.readframes(frames_per_chunk)
                    frames_read = len(pcm_bytes) // bytes_per_frame
                    if frames_read == 0:
                        break

                    end_frame = start_frame + frames_read
                    yield AudioChunk(
                        start_seconds=start_frame / self.metadata.sample_rate,
                        end_seconds=end_frame / self.metadata.sample_rate,
                        pcm_bytes=pcm_bytes,
                    )
                    start_frame = end_frame
        except (EOFError, wave.Error) as exc:
            raise InvalidWavFileError(
                f"File is not a valid WAV file: {self.path}"
            ) from exc

    def _read_metadata(self) -> AudioMetadata:
        if not self.path.is_file():
            raise FileNotFoundError(f"WAV file not found: {self.path}")

        try:
            with wave.open(str(self.path), "rb") as wav_file:
                sample_rate = wav_file.getframerate()
                channel_count = wav_file.getnchannels()
                sample_width_bytes = wav_file.getsampwidth()
                frame_count = wav_file.getnframes()
        except (EOFError, wave.Error) as exc:
            raise InvalidWavFileError(
                f"File is not a valid WAV file: {self.path}"
            ) from exc

        return AudioMetadata(
            path=self.path,
            sample_rate=sample_rate,
            channel_count=channel_count,
            sample_width_bytes=sample_width_bytes,
            frame_count=frame_count,
            duration_seconds=frame_count / sample_rate,
        )

    def _frames_per_chunk(self, chunk_duration_seconds: float) -> int:
        if chunk_duration_seconds <= 0:
            raise ValueError("chunk_duration_seconds must be greater than 0")

        frames_per_chunk = int(self.metadata.sample_rate * chunk_duration_seconds)
        if frames_per_chunk < 1:
            raise ValueError(
                "chunk_duration_seconds must be long enough to include at least "
                "one audio frame"
            )

        return frames_per_chunk
