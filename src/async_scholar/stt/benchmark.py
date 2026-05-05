"""File STT benchmark harness.

This module intentionally requires every benchmark input explicitly. It does
not choose product model defaults.
"""

from __future__ import annotations

import argparse
import json
import time
import wave
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from async_scholar.file_transcription import transcribe_file_to_artifacts

BENCHMARK_REPORT_NAME = "benchmark-report.json"


@dataclass(frozen=True)
class BenchmarkResult:
    """Result metadata for one benchmark run."""

    report_path: Path
    report: dict[str, Any]


def run_benchmark(
    audio_path: str | Path,
    *,
    model_size_or_path: str,
    output_root: str | Path,
    transcriber_factory: object | None = None,
    clock: Callable[[], float] = time.perf_counter,
) -> BenchmarkResult:
    """Run file transcription once and write a privacy-safe benchmark report."""

    audio = Path(audio_path)
    output = Path(output_root)
    started_at = datetime.now(UTC)
    start = clock()
    transcription_result = transcribe_file_to_artifacts(
        audio,
        model_size_or_path=model_size_or_path,
        output_root=output,
        transcriber_factory=transcriber_factory,
    )
    elapsed_seconds = max(0.0, clock() - start)

    artifact_paths = transcription_result.artifact_paths
    report_path = artifact_paths.output_dir / BENCHMARK_REPORT_NAME
    audio_duration_seconds = _read_wav_duration_seconds(audio)
    real_time_factor = _real_time_factor(elapsed_seconds, audio_duration_seconds)

    report = _build_report(
        audio_path=audio,
        model_size_or_path=model_size_or_path,
        started_at=started_at,
        elapsed_seconds=elapsed_seconds,
        audio_duration_seconds=audio_duration_seconds,
        real_time_factor=real_time_factor,
        session_id=transcription_result.session_id,
        segment_count=transcription_result.segment_count,
        output_dir=artifact_paths.output_dir,
        transcript_jsonl_path=artifact_paths.transcript_jsonl_path,
        transcript_markdown_path=artifact_paths.transcript_markdown_path,
        report_path=report_path,
    )

    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return BenchmarkResult(report_path=report_path, report=report)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the benchmark CLI."""

    args = _build_parser().parse_args(argv)
    result = run_benchmark(
        args.audio_path,
        model_size_or_path=args.model_size_or_path,
        output_root=args.output_root,
    )
    print(f"Wrote benchmark report: {result.report_path}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Benchmark one explicit file STT transcription run.",
    )
    parser.add_argument(
        "--audio-path",
        required=True,
        type=Path,
        help="Existing local audio file to transcribe.",
    )
    parser.add_argument(
        "--model-size-or-path",
        required=True,
        help="Explicit faster-whisper model size or model path.",
    )
    parser.add_argument(
        "--output-root",
        required=True,
        type=Path,
        help="Directory where transcript artifacts and report will be written.",
    )
    return parser


def _build_report(
    *,
    audio_path: Path,
    model_size_or_path: str,
    started_at: datetime,
    elapsed_seconds: float,
    audio_duration_seconds: float | None,
    real_time_factor: float | None,
    session_id: str,
    segment_count: int,
    output_dir: Path,
    transcript_jsonl_path: Path,
    transcript_markdown_path: Path,
    report_path: Path,
) -> dict[str, Any]:
    duration_status = (
        "available" if audio_duration_seconds is not None else "unavailable"
    )
    return {
        "schema_version": 1,
        "input": {
            "audio_file_name": audio_path.name,
            "audio_duration_seconds": _rounded_or_none(audio_duration_seconds),
            "audio_duration_status": duration_status,
            "audio_duration_source": (
                "wav_header" if audio_duration_seconds is not None else "unavailable"
            ),
        },
        "model": _model_reference(model_size_or_path),
        "timing": {
            "started_at_utc": _iso_utc(started_at),
            "elapsed_seconds": round(elapsed_seconds, 6),
            "real_time_factor": _rounded_or_none(real_time_factor),
            "notes": (
                "elapsed_seconds covers model setup, transcription, and artifact "
                "writing; separate model-load timing is not measured by this "
                "skeleton."
            ),
        },
        "transcript": {
            "session_id": session_id,
            "segment_count": segment_count,
        },
        "artifacts": {
            "output_dir": ".",
            "transcript_jsonl": _relative_or_name(transcript_jsonl_path, output_dir),
            "transcript_markdown": _relative_or_name(
                transcript_markdown_path,
                output_dir,
            ),
            "benchmark_report": _relative_or_name(report_path, output_dir),
        },
        "unavailable_metrics": {
            "model_load_seconds": {
                "value": None,
                "status": "unavailable",
                "reason": "not measured separately by this skeleton",
            },
            "peak_ram_bytes": {
                "value": None,
                "status": "future_work",
                "reason": "memory sampling is not implemented",
            },
            "gpu_utilization": {
                "value": None,
                "status": "future_work",
                "reason": "GPU telemetry is not implemented",
            },
        },
    }


def _read_wav_duration_seconds(audio_path: Path) -> float | None:
    try:
        with wave.open(str(audio_path), "rb") as wav_file:
            frame_rate = wav_file.getframerate()
            frame_count = wav_file.getnframes()
    except (EOFError, OSError, wave.Error):
        return None

    if frame_rate <= 0 or frame_count < 0:
        return None
    return frame_count / frame_rate


def _real_time_factor(
    elapsed_seconds: float,
    audio_duration_seconds: float | None,
) -> float | None:
    if audio_duration_seconds is None or audio_duration_seconds <= 0:
        return None
    return elapsed_seconds / audio_duration_seconds


def _model_reference(model_size_or_path: str) -> dict[str, Any]:
    value = model_size_or_path.strip()
    path_like = _is_private_path_like(value)
    if path_like:
        reference = PureWindowsPath(value).name or PurePosixPath(value).name or "<path>"
    else:
        reference = value
    return {
        "reference": reference,
        "path_like_reference_redacted": path_like,
    }


def _is_private_path_like(value: str) -> bool:
    windows_path = PureWindowsPath(value)
    posix_path = PurePosixPath(value)
    return (
        windows_path.is_absolute()
        or posix_path.is_absolute()
        or bool(windows_path.drive)
        or value.startswith("~")
        or value.startswith(".")
        or "\\" in value
    )


def _relative_or_name(path: Path, base: Path) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.name


def _rounded_or_none(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 6)


def _iso_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
