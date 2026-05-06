"""Pure diagnostics for planned audio chunk backlog pressure."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from math import isfinite
from numbers import Real

DEFAULT_SUSTAINED_BACKLOG_THRESHOLD_SECONDS = 10.0
FILE_INPUT_BACKPRESSURE_RECOMMENDATION = "pause_file_input"


def _validate_finite_non_negative(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{field_name} must be a finite non-negative number")

    number = float(value)
    if not isfinite(number):
        raise ValueError(f"{field_name} must be finite")
    if number < 0.0:
        raise ValueError(f"{field_name} must be non-negative")

    return number


@dataclass(frozen=True)
class BackpressureConfig:
    """Configuration for deterministic audio backlog diagnostics."""

    sustained_backlog_threshold_seconds: float = (
        DEFAULT_SUSTAINED_BACKLOG_THRESHOLD_SECONDS
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "sustained_backlog_threshold_seconds",
            _validate_finite_non_negative(
                self.sustained_backlog_threshold_seconds,
                "sustained_backlog_threshold_seconds",
            ),
        )


DEFAULT_BACKPRESSURE_CONFIG = BackpressureConfig()


@dataclass(frozen=True)
class BackpressureSnapshot:
    """Observed planned chunk backlog state."""

    pending_chunks: Sequence[object]
    oldest_pending_age_seconds: float
    observed_at_seconds: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "pending_chunks",
            _normalize_pending_chunks(self.pending_chunks),
        )
        object.__setattr__(
            self,
            "oldest_pending_age_seconds",
            _validate_finite_non_negative(
                self.oldest_pending_age_seconds,
                "oldest_pending_age_seconds",
            ),
        )
        object.__setattr__(
            self,
            "observed_at_seconds",
            _validate_finite_non_negative(
                self.observed_at_seconds,
                "observed_at_seconds",
            ),
        )


@dataclass(frozen=True)
class AudioBackpressureDiagnostic:
    """Safe metadata summary for sustained audio chunk backlog."""

    pending_chunk_count: int
    queued_audio_seconds: float
    oldest_pending_age_seconds: float
    observed_at_seconds: float
    sustained_backlog_threshold_seconds: float
    recommended_action: str

    def __post_init__(self) -> None:
        if isinstance(self.pending_chunk_count, bool) or not isinstance(
            self.pending_chunk_count, int
        ):
            raise TypeError("pending_chunk_count must be a non-negative integer")
        if self.pending_chunk_count < 0:
            raise ValueError("pending_chunk_count must be non-negative")

        object.__setattr__(
            self,
            "queued_audio_seconds",
            _validate_finite_non_negative(
                self.queued_audio_seconds,
                "queued_audio_seconds",
            ),
        )
        object.__setattr__(
            self,
            "oldest_pending_age_seconds",
            _validate_finite_non_negative(
                self.oldest_pending_age_seconds,
                "oldest_pending_age_seconds",
            ),
        )
        object.__setattr__(
            self,
            "observed_at_seconds",
            _validate_finite_non_negative(
                self.observed_at_seconds,
                "observed_at_seconds",
            ),
        )
        object.__setattr__(
            self,
            "sustained_backlog_threshold_seconds",
            _validate_finite_non_negative(
                self.sustained_backlog_threshold_seconds,
                "sustained_backlog_threshold_seconds",
            ),
        )
        if not isinstance(self.recommended_action, str):
            raise TypeError("recommended_action must be a string")


def evaluate_audio_backpressure(
    snapshot: BackpressureSnapshot,
    config: BackpressureConfig = DEFAULT_BACKPRESSURE_CONFIG,
) -> AudioBackpressureDiagnostic | None:
    """Return a safe diagnostic when planned STT chunks have backed up."""

    if not isinstance(snapshot, BackpressureSnapshot):
        raise TypeError("snapshot must be a BackpressureSnapshot")
    if not isinstance(config, BackpressureConfig):
        raise TypeError("config must be a BackpressureConfig")

    if not snapshot.pending_chunks:
        return None

    queued_audio_seconds = _queued_audio_seconds(snapshot.pending_chunks)
    if snapshot.oldest_pending_age_seconds < config.sustained_backlog_threshold_seconds:
        return None

    return AudioBackpressureDiagnostic(
        pending_chunk_count=len(snapshot.pending_chunks),
        queued_audio_seconds=queued_audio_seconds,
        oldest_pending_age_seconds=snapshot.oldest_pending_age_seconds,
        observed_at_seconds=snapshot.observed_at_seconds,
        sustained_backlog_threshold_seconds=(
            config.sustained_backlog_threshold_seconds
        ),
        recommended_action=FILE_INPUT_BACKPRESSURE_RECOMMENDATION,
    )


def _queued_audio_seconds(chunks: Sequence[object]) -> float:
    return sum(
        _chunk_duration_seconds(chunk, f"pending_chunks[{index}]")
        for index, chunk in enumerate(chunks)
    )


def _chunk_duration_seconds(chunk: object, field_name: str) -> float:
    if hasattr(chunk, "duration_seconds"):
        return _validate_finite_non_negative(
            chunk.duration_seconds,
            f"{field_name}.duration_seconds",
        )

    try:
        start_seconds = chunk.start_seconds
        end_seconds = chunk.end_seconds
    except AttributeError as exc:
        raise TypeError(
            f"{field_name} must expose duration_seconds or "
            "start_seconds and end_seconds"
        ) from exc

    start_seconds = _validate_finite_non_negative(
        start_seconds,
        f"{field_name}.start_seconds",
    )
    end_seconds = _validate_finite_non_negative(
        end_seconds,
        f"{field_name}.end_seconds",
    )
    if end_seconds < start_seconds:
        raise ValueError(
            f"{field_name}.end_seconds must be greater than or equal to start_seconds"
        )

    return end_seconds - start_seconds


def _normalize_pending_chunks(pending_chunks: Iterable[object]) -> tuple[object, ...]:
    if isinstance(pending_chunks, str | bytes):
        raise TypeError("pending_chunks must be a sequence of chunk windows")

    try:
        return tuple(pending_chunks)
    except TypeError as exc:
        raise TypeError("pending_chunks must be a sequence of chunk windows") from exc
