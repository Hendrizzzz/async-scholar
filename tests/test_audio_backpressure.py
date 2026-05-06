from __future__ import annotations

from dataclasses import dataclass, fields
from math import inf

import pytest

from async_scholar.audio import (
    DEFAULT_BACKPRESSURE_CONFIG,
    DEFAULT_SUSTAINED_BACKLOG_THRESHOLD_SECONDS,
    FILE_INPUT_BACKPRESSURE_RECOMMENDATION,
    AudioBackpressureDiagnostic,
    BackpressureConfig,
    BackpressureSnapshot,
    SttChunkWindow,
    evaluate_audio_backpressure,
)


@dataclass(frozen=True)
class DurationOnlyChunk:
    duration_seconds: float


@dataclass(frozen=True)
class WindowLike:
    start_seconds: float
    end_seconds: float


@dataclass(frozen=True)
class ChunkWithPrivateData:
    duration_seconds: float
    transcript_text: str
    audio_bytes: bytes
    file_path: str
    model_path: str


def stt_chunk(start_seconds: float, end_seconds: float) -> SttChunkWindow:
    return SttChunkWindow(start_seconds=start_seconds, end_seconds=end_seconds)


def snapshot(
    pending_chunks: list[object],
    oldest_pending_age_seconds: float,
) -> BackpressureSnapshot:
    return BackpressureSnapshot(
        pending_chunks=pending_chunks,
        oldest_pending_age_seconds=oldest_pending_age_seconds,
        observed_at_seconds=42.0,
    )


def test_default_threshold_matches_phase_three_guidance() -> None:
    assert pytest.approx(10.0) == DEFAULT_SUSTAINED_BACKLOG_THRESHOLD_SECONDS
    assert pytest.approx(10.0) == (
        DEFAULT_BACKPRESSURE_CONFIG.sustained_backlog_threshold_seconds
    )


def test_no_pending_chunks_returns_no_diagnostic() -> None:
    assert evaluate_audio_backpressure(snapshot([], 30.0)) is None


def test_pending_backlog_below_threshold_returns_no_diagnostic() -> None:
    result = evaluate_audio_backpressure(snapshot([stt_chunk(0.0, 4.0)], 9.999))

    assert result is None


def test_threshold_crossing_backlog_returns_safe_summary() -> None:
    result = evaluate_audio_backpressure(snapshot([stt_chunk(0.0, 4.0)], 10.0))

    assert result == AudioBackpressureDiagnostic(
        pending_chunk_count=1,
        queued_audio_seconds=4.0,
        oldest_pending_age_seconds=10.0,
        observed_at_seconds=42.0,
        sustained_backlog_threshold_seconds=10.0,
        recommended_action=FILE_INPUT_BACKPRESSURE_RECOMMENDATION,
    )


def test_queued_audio_duration_uses_stt_chunk_windows() -> None:
    result = evaluate_audio_backpressure(
        snapshot(
            [
                stt_chunk(1.0, 9.0),
                stt_chunk(12.0, 17.5),
            ],
            12.0,
        )
    )

    assert result is not None
    assert result.pending_chunk_count == 2
    assert result.queued_audio_seconds == pytest.approx(13.5)


def test_file_input_recommendation_is_deterministic() -> None:
    result = evaluate_audio_backpressure(snapshot([DurationOnlyChunk(8.0)], 11.0))

    assert result is not None
    assert result.recommended_action == "pause_file_input"


def test_diagnostic_contains_safe_metadata_only() -> None:
    result = evaluate_audio_backpressure(
        snapshot(
            [
                ChunkWithPrivateData(
                    duration_seconds=8.0,
                    transcript_text="private transcript text",
                    audio_bytes=b"private-audio-bytes",
                    file_path="C:\\private\\lecture.wav",
                    model_path="C:\\private\\model.bin",
                )
            ],
            12.0,
        )
    )

    assert result is not None
    diagnostic_field_names = {field.name for field in fields(result)}
    assert diagnostic_field_names == {
        "pending_chunk_count",
        "queued_audio_seconds",
        "oldest_pending_age_seconds",
        "observed_at_seconds",
        "sustained_backlog_threshold_seconds",
        "recommended_action",
    }
    diagnostic_text = repr(result)
    assert "pending_chunks" not in diagnostic_text
    assert "private transcript text" not in diagnostic_text
    assert "private-audio-bytes" not in diagnostic_text
    assert "lecture.wav" not in diagnostic_text
    assert "model.bin" not in diagnostic_text


@pytest.mark.parametrize(
    ("config", "error_type", "match"),
    [
        (
            {"sustained_backlog_threshold_seconds": -0.1},
            ValueError,
            "sustained_backlog_threshold_seconds",
        ),
        (
            {"sustained_backlog_threshold_seconds": inf},
            ValueError,
            "sustained_backlog_threshold_seconds",
        ),
        (
            {"sustained_backlog_threshold_seconds": True},
            TypeError,
            "sustained_backlog_threshold_seconds",
        ),
    ],
)
def test_rejects_invalid_config(
    config: dict[str, object],
    error_type: type[Exception],
    match: str,
) -> None:
    with pytest.raises(error_type, match=match):
        BackpressureConfig(**config)


@pytest.mark.parametrize(
    ("kwargs", "error_type", "match"),
    [
        (
            {"oldest_pending_age_seconds": -0.1, "observed_at_seconds": 0.0},
            ValueError,
            "oldest_pending_age_seconds",
        ),
        (
            {"oldest_pending_age_seconds": 0.0, "observed_at_seconds": inf},
            ValueError,
            "observed_at_seconds",
        ),
        (
            {"pending_chunks": object()},
            TypeError,
            "pending_chunks",
        ),
    ],
)
def test_rejects_invalid_snapshot(
    kwargs: dict[str, object],
    error_type: type[Exception],
    match: str,
) -> None:
    base_kwargs: dict[str, object] = {
        "pending_chunks": [],
        "oldest_pending_age_seconds": 0.0,
        "observed_at_seconds": 0.0,
    }
    base_kwargs.update(kwargs)

    with pytest.raises(error_type, match=match):
        BackpressureSnapshot(**base_kwargs)


@pytest.mark.parametrize(
    ("pending_chunks", "error_type", "match"),
    [
        ([object()], TypeError, "duration_seconds or start_seconds"),
        ([DurationOnlyChunk(-1.0)], ValueError, "duration_seconds"),
        ([DurationOnlyChunk(inf)], ValueError, "duration_seconds"),
        ([WindowLike(2.0, 1.0)], ValueError, "greater than or equal"),
        ([WindowLike(-1.0, 1.0)], ValueError, "start_seconds"),
    ],
)
def test_rejects_invalid_pending_chunk_values(
    pending_chunks: list[object],
    error_type: type[Exception],
    match: str,
) -> None:
    with pytest.raises(error_type, match=match):
        evaluate_audio_backpressure(snapshot(pending_chunks, 10.0))
