from __future__ import annotations

from dataclasses import dataclass
from math import inf

import pytest

from async_scholar.audio import (
    DEFAULT_VAD_CHUNKING_CONFIG,
    SpeechWindow,
    SttChunkWindow,
    VadChunkingConfig,
    aggregate_speech_windows,
)


@dataclass(frozen=True)
class WindowLike:
    start_seconds: float
    end_seconds: float


def speech_window(start_seconds: float, end_seconds: float) -> SpeechWindow:
    return SpeechWindow(start_seconds=start_seconds, end_seconds=end_seconds)


def assert_chunk(
    chunk: SttChunkWindow,
    start_seconds: float,
    end_seconds: float,
) -> None:
    assert chunk.start_seconds == pytest.approx(start_seconds)
    assert chunk.end_seconds == pytest.approx(end_seconds)


def test_default_chunking_config_matches_phase_three_plan() -> None:
    assert (
        VadChunkingConfig(
            pre_roll_seconds=0.5,
            post_roll_seconds=0.8,
            minimum_window_seconds=8.0,
            target_window_seconds=15.0,
            maximum_window_seconds=30.0,
            overlap_seconds=1.0,
            max_silence_before_flush_seconds=2.0,
        )
        == DEFAULT_VAD_CHUNKING_CONFIG
    )


def test_empty_input_returns_no_chunks() -> None:
    assert aggregate_speech_windows([]) == []


def test_merges_nearby_speech_windows_and_pads_to_minimum() -> None:
    chunks = aggregate_speech_windows(
        [
            speech_window(1.0, 2.0),
            speech_window(3.0, 4.5),
        ]
    )

    assert len(chunks) == 1
    assert_chunk(chunks[0], 0.5, 8.5)


def test_separated_speech_windows_flush_to_separate_chunks() -> None:
    chunks = aggregate_speech_windows(
        [
            speech_window(10.0, 11.0),
            speech_window(25.0, 26.0),
        ]
    )

    assert len(chunks) == 2
    assert_chunk(chunks[0], 9.5, 17.5)
    assert_chunk(chunks[1], 24.5, 32.5)


def test_applies_pre_roll_and_post_roll_without_minimum_padding() -> None:
    config = VadChunkingConfig(minimum_window_seconds=0.0)

    chunks = aggregate_speech_windows([speech_window(2.0, 4.0)], config=config)

    assert len(chunks) == 1
    assert_chunk(chunks[0], 1.5, 4.8)


def test_minimum_duration_padding_extends_end_first() -> None:
    config = VadChunkingConfig(pre_roll_seconds=0.0, post_roll_seconds=0.0)

    chunks = aggregate_speech_windows([speech_window(10.0, 11.0)], config=config)

    assert len(chunks) == 1
    assert chunks[0].duration_seconds == pytest.approx(8.0)
    assert_chunk(chunks[0], 10.0, 18.0)


def test_maximum_duration_splits_long_windows_with_overlap() -> None:
    config = VadChunkingConfig(
        pre_roll_seconds=0.0,
        post_roll_seconds=0.0,
        minimum_window_seconds=8.0,
        target_window_seconds=15.0,
        maximum_window_seconds=30.0,
        overlap_seconds=1.0,
    )

    chunks = aggregate_speech_windows([speech_window(0.0, 40.0)], config=config)

    assert len(chunks) == 2
    assert_chunk(chunks[0], 0.0, 30.0)
    assert_chunk(chunks[1], 29.0, 40.0)
    assert chunks[0].end_seconds - chunks[1].start_seconds == pytest.approx(1.0)


def test_target_flush_uses_overlap_for_adjacent_context_chunks() -> None:
    config = VadChunkingConfig(
        pre_roll_seconds=0.5,
        post_roll_seconds=0.0,
        minimum_window_seconds=8.0,
        target_window_seconds=10.0,
        maximum_window_seconds=30.0,
        overlap_seconds=1.0,
    )

    chunks = aggregate_speech_windows(
        [
            speech_window(2.0, 11.0),
            speech_window(12.0, 13.0),
        ],
        config=config,
    )

    assert len(chunks) == 2
    assert_chunk(chunks[0], 1.5, 11.0)
    assert_chunk(chunks[1], 10.5, 18.5)
    assert chunks[1].start_seconds < chunks[0].end_seconds


def test_clamps_end_to_audio_duration_and_expands_start_when_needed() -> None:
    chunks = aggregate_speech_windows(
        [speech_window(6.0, 9.8)],
        audio_duration_seconds=10.0,
    )

    assert len(chunks) == 1
    assert_chunk(chunks[0], 2.0, 10.0)


@pytest.mark.parametrize(
    ("speech_windows", "match"),
    [
        ([speech_window(2.0, 3.0), speech_window(1.0, 2.0)], "ordered"),
        ([WindowLike(-1.0, 1.0)], "non-negative"),
        ([WindowLike(0.0, inf)], "finite"),
        ([WindowLike(2.0, 1.0)], "greater than or equal"),
    ],
)
def test_rejects_invalid_speech_windows(
    speech_windows: list[SpeechWindow | WindowLike],
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        aggregate_speech_windows(speech_windows)


def test_rejects_missing_speech_window_attributes() -> None:
    with pytest.raises(TypeError, match="start_seconds and end_seconds"):
        aggregate_speech_windows([object()])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"pre_roll_seconds": -0.1},
        {"minimum_window_seconds": 16.0, "target_window_seconds": 15.0},
        {"target_window_seconds": 31.0, "maximum_window_seconds": 30.0},
        {"maximum_window_seconds": 0.0},
        {"overlap_seconds": 30.0, "maximum_window_seconds": 30.0},
    ],
)
def test_rejects_invalid_chunking_config(kwargs: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        VadChunkingConfig(**kwargs)


def test_rejects_invalid_audio_duration() -> None:
    with pytest.raises(ValueError, match="audio_duration_seconds"):
        aggregate_speech_windows(
            [speech_window(0.0, 1.0)],
            audio_duration_seconds=-1.0,
        )
