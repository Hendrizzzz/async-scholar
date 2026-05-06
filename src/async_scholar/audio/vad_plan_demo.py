"""Privacy-safe file VAD planning demo runner."""

from __future__ import annotations

import argparse
import json
import math
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Any

REPORT_FILENAME = "vad-plan-report.json"

SpeechDetector = Callable[[Path], Iterable[object]]
ChunkPlanner = Callable[..., Sequence[object]]


def run_vad_plan_demo(
    audio_path: str | Path,
    output_root: str | Path,
    *,
    speech_detector: SpeechDetector | None = None,
    chunk_planner: ChunkPlanner | None = None,
    oldest_pending_age_seconds: float | None = None,
    observed_at_seconds: float = 0.0,
) -> Path:
    """Plan file VAD chunks and write a privacy-safe report."""
    audio_file = _required_path(audio_path, "audio path")
    output_dir = _required_path(output_root, "output root")

    if not audio_file.is_file():
        raise FileNotFoundError("audio path does not exist or is not a file")

    detector = speech_detector or _load_default_speech_detector()
    planner = chunk_planner or _load_default_chunk_planner()
    speech_windows: list[object] = []
    detector_called = False

    def recording_detector(path: Path) -> list[object]:
        nonlocal detector_called, speech_windows
        detector_called = True
        speech_windows = list(detector(path))
        return speech_windows

    chunks = list(planner(audio_file, speech_detector=recording_detector))
    if not detector_called:
        speech_windows = recording_detector(audio_file)

    report = _build_report(
        speech_windows=speech_windows,
        chunks=chunks,
        oldest_pending_age_seconds=oldest_pending_age_seconds,
        observed_at_seconds=observed_at_seconds,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / REPORT_FILENAME
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create a privacy-safe VAD planning report from one explicit "
            "local audio file."
        )
    )
    parser.add_argument(
        "--audio-path",
        required=True,
        help="Existing local audio file to analyze.",
    )
    parser.add_argument(
        "--output-root",
        required=True,
        help="Directory that will receive vad-plan-report.json.",
    )
    parser.add_argument(
        "--oldest-pending-age-seconds",
        type=float,
        default=None,
        help="Include backlog diagnostic metadata using this queued age.",
    )
    parser.add_argument(
        "--observed-at-seconds",
        type=float,
        default=0.0,
        help="Stable observation timestamp for optional backlog metadata.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        report_path = run_vad_plan_demo(
            args.audio_path,
            args.output_root,
            oldest_pending_age_seconds=args.oldest_pending_age_seconds,
            observed_at_seconds=args.observed_at_seconds,
        )
    except (FileNotFoundError, TypeError, ValueError) as exc:
        parser.exit(1, f"error: {exc}\n")

    print(f"Wrote {report_path.name}")
    return 0


def _load_default_speech_detector() -> SpeechDetector:
    from async_scholar.audio.vad import detect_speech_windows

    return detect_speech_windows


def _load_default_chunk_planner() -> ChunkPlanner:
    from async_scholar.file_transcription import plan_file_transcription_chunks

    return plan_file_transcription_chunks


def _build_report(
    *,
    speech_windows: Sequence[object],
    chunks: Sequence[object],
    oldest_pending_age_seconds: float | None,
    observed_at_seconds: float,
) -> dict[str, Any]:
    chunk_summary = _summarize_windows(chunks)
    return {
        "report_version": 1,
        "report_name": REPORT_FILENAME,
        "artifact_names": [REPORT_FILENAME],
        "speech": _summarize_windows(speech_windows),
        "chunks": {
            **chunk_summary,
            "queued_audio_seconds": chunk_summary["total_duration_seconds"],
            "timing_windows": _window_rows(chunks),
        },
        "backpressure": _backpressure_metadata(
            chunks=chunks,
            oldest_pending_age_seconds=oldest_pending_age_seconds,
            observed_at_seconds=observed_at_seconds,
        ),
    }


def _summarize_windows(windows: Sequence[object]) -> dict[str, Any]:
    pairs = [_window_pair(window) for window in windows]
    durations = [_round_seconds(end - start) for start, end in pairs]

    if not pairs:
        return {
            "count": 0,
            "total_duration_seconds": 0.0,
            "first_start_seconds": None,
            "last_end_seconds": None,
            "min_duration_seconds": None,
            "max_duration_seconds": None,
        }

    starts = [start for start, _ in pairs]
    ends = [end for _, end in pairs]
    return {
        "count": len(pairs),
        "total_duration_seconds": _round_seconds(sum(durations)),
        "first_start_seconds": _round_seconds(min(starts)),
        "last_end_seconds": _round_seconds(max(ends)),
        "min_duration_seconds": min(durations),
        "max_duration_seconds": max(durations),
    }


def _window_rows(windows: Sequence[object]) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for window in windows:
        start, end = _window_pair(window)
        rows.append(
            {
                "start_seconds": _round_seconds(start),
                "end_seconds": _round_seconds(end),
                "duration_seconds": _round_seconds(end - start),
            }
        )
    return rows


def _backpressure_metadata(
    *,
    chunks: Sequence[object],
    oldest_pending_age_seconds: float | None,
    observed_at_seconds: float,
) -> dict[str, Any]:
    if oldest_pending_age_seconds is None:
        return {"evaluated": False, "diagnostic": None}

    from async_scholar.audio.backpressure import (
        BackpressureSnapshot,
        evaluate_audio_backpressure,
    )

    snapshot = BackpressureSnapshot(
        pending_chunks=chunks,
        oldest_pending_age_seconds=oldest_pending_age_seconds,
        observed_at_seconds=observed_at_seconds,
    )
    diagnostic = evaluate_audio_backpressure(snapshot)
    if diagnostic is None:
        diagnostic_metadata = None
    else:
        diagnostic_metadata = _round_metadata(asdict(diagnostic))
    return {"evaluated": True, "diagnostic": diagnostic_metadata}


def _required_path(value: str | Path, label: str) -> Path:
    if isinstance(value, str) and not value.strip():
        raise ValueError(f"{label} is required")
    return Path(value)


def _window_pair(window: object) -> tuple[float, float]:
    start = _window_value(window, "start_seconds")
    end = _window_value(window, "end_seconds")
    if end < start:
        raise ValueError("window end must be greater than or equal to start")
    return start, end


def _window_value(window: object, name: str) -> float:
    if isinstance(window, Mapping):
        value = window.get(name)
    else:
        value = getattr(window, name, None)
    if not isinstance(value, int | float):
        raise TypeError(f"window {name} must be numeric")

    seconds = float(value)
    if not math.isfinite(seconds) or seconds < 0:
        raise ValueError(f"window {name} must be finite and non-negative")
    return seconds


def _round_metadata(value: Any) -> Any:
    if isinstance(value, float):
        return _round_seconds(value)
    if isinstance(value, dict):
        return {key: _round_metadata(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_round_metadata(item) for item in value]
    return value


def _round_seconds(value: float) -> float:
    return round(float(value), 6)


if __name__ == "__main__":
    raise SystemExit(main())
