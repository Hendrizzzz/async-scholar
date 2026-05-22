"""Metadata-only audio evidence manifest helpers."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from pathlib import Path
from typing import Any

ALLOWED_EVIDENCE_KINDS = frozenset(
    {
        "public_open_speech",
        "bounded_local_microphone",
        "synthetic_audio_fixture",
    }
)
ALLOWED_SOURCE_METADATA_KEYS = frozenset(
    {
        "bit_depth",
        "channel_count",
        "encoding",
        "language",
        "sample_rate_hz",
        "source_family",
    }
)
_SOURCE_TEXT_BY_EVIDENCE_KIND = {
    "public_open_speech": {
        "labels": frozenset({"Open Speech Repository Hindi sample"}),
        "attributions": frozenset(
            {"Open Speech Repository source identification required"}
        ),
    },
    "bounded_local_microphone": {
        "labels": frozenset({"Bounded local microphone evidence"}),
        "attributions": frozenset(
            {"User-confirmed bounded local microphone diagnostic"}
        ),
    },
    "synthetic_audio_fixture": {
        "labels": frozenset({"Synthetic audio fixture"}),
        "attributions": frozenset({"AsyncScholar local test fixture"}),
    },
}
_ALLOWED_SOURCE_METADATA_STRING_VALUES = {
    "encoding": frozenset({"PCM"}),
    "language": frozenset({"Hindi"}),
    "source_family": frozenset(
        {
            "bounded_local_microphone",
            "public_open_speech",
            "synthetic_audio_fixture",
        }
    ),
}


class AudioEvidenceManifestError(ValueError):
    """Raised for sanitized audio evidence manifest failures."""


def build_audio_evidence_manifest(
    *,
    evidence_kind: str,
    source_label: str,
    source_attribution: str,
    source_metadata: Mapping[str, object] | None = None,
    source_audio_path: str | Path | None = None,
    vad_report_path: str | Path | None = None,
    benchmark_report_path: str | Path | None = None,
    transcript_jsonl_path: str | Path | None = None,
    transcript_markdown_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build a JSON-ready manifest from safe report metadata.

    Source audio and transcript artifact paths are used only for presence
    booleans. Their contents, filenames, paths, sizes, and hashes are never
    read or serialized by this helper.
    """

    kind = _safe_evidence_kind(evidence_kind)
    vad_present = _is_present(vad_report_path)
    benchmark_present = _is_present(benchmark_report_path)
    vad_report = _read_report(vad_report_path, "vad") if vad_present else None
    benchmark_report = (
        _read_report(benchmark_report_path, "benchmark") if benchmark_present else None
    )

    return {
        "schema_version": 1,
        "evidence_kind": kind,
        "source": {
            "label": _safe_text(
                source_label,
                "source label",
                allowed_values=_SOURCE_TEXT_BY_EVIDENCE_KIND[kind]["labels"],
            ),
            "attribution": _safe_text(
                source_attribution,
                "source attribution",
                allowed_values=_SOURCE_TEXT_BY_EVIDENCE_KIND[kind]["attributions"],
            ),
            "metadata": _safe_source_metadata(source_metadata or {}),
        },
        "artifacts": {
            "source_audio_present": _is_present(source_audio_path),
            "vad_report_present": vad_present,
            "benchmark_report_present": benchmark_present,
            "transcript_jsonl_present": _is_present(transcript_jsonl_path),
            "transcript_markdown_present": _is_present(transcript_markdown_path),
        },
        "audio": _audio_metadata(benchmark_report),
        "vad": _vad_metadata(vad_report),
        "stt": _stt_metadata(benchmark_report),
    }


def _safe_evidence_kind(value: str) -> str:
    if value not in ALLOWED_EVIDENCE_KINDS:
        raise AudioEvidenceManifestError(
            "audio evidence manifest evidence kind is invalid"
        )
    return value


def _safe_text(
    value: str,
    label: str,
    *,
    allowed_values: frozenset[str],
) -> str:
    if not isinstance(value, str):
        raise AudioEvidenceManifestError(f"audio evidence manifest {label} is invalid")
    normalized = " ".join(value.split())
    if not normalized or len(normalized) > 120:
        raise AudioEvidenceManifestError(f"audio evidence manifest {label} is invalid")
    if normalized not in allowed_values:
        raise AudioEvidenceManifestError(f"audio evidence manifest {label} is invalid")
    return normalized


def _safe_source_metadata(metadata: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(metadata, Mapping):
        raise AudioEvidenceManifestError(
            "audio evidence manifest source metadata is invalid"
        )

    safe: dict[str, object] = {}
    for key, value in metadata.items():
        if key not in ALLOWED_SOURCE_METADATA_KEYS:
            raise AudioEvidenceManifestError(
                "audio evidence manifest source metadata is invalid"
            )
        safe[key] = _safe_source_metadata_value_for_key(key, value)
    return safe


def _safe_source_metadata_value_for_key(key: str, value: object) -> object:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int | float):
        numeric = float(value)
        if not math.isfinite(numeric):
            raise AudioEvidenceManifestError(
                "audio evidence manifest source metadata is invalid"
            )
        return value
    if isinstance(value, str):
        return _safe_text(
            value,
            "source metadata",
            allowed_values=_ALLOWED_SOURCE_METADATA_STRING_VALUES.get(
                key,
                frozenset(),
            ),
        )
    raise AudioEvidenceManifestError(
        "audio evidence manifest source metadata is invalid"
    )


def _is_present(path: str | Path | None) -> bool:
    if path is None:
        return False
    return Path(path).is_file()


def _read_report(path: str | Path | None, report_kind: str) -> Mapping[str, Any]:
    if path is None:
        raise AudioEvidenceManifestError(
            f"audio evidence manifest {report_kind} report could not be parsed"
        )
    try:
        report = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise AudioEvidenceManifestError(
            f"audio evidence manifest {report_kind} report could not be parsed"
        ) from None
    if not isinstance(report, Mapping):
        raise AudioEvidenceManifestError(
            f"audio evidence manifest {report_kind} report is invalid"
        )
    return report


def _audio_metadata(report: Mapping[str, Any] | None) -> dict[str, object]:
    if report is None:
        return {"duration_seconds": None, "duration_status": None}

    input_metadata = _nested_mapping(report, "input", report_kind="benchmark")
    return {
        "duration_seconds": _optional_nonnegative_number(
            input_metadata.get("audio_duration_seconds"),
            report_kind="benchmark",
        ),
        "duration_status": _optional_safe_status(
            input_metadata.get("audio_duration_status"),
            report_kind="benchmark",
        ),
    }


def _vad_metadata(report: Mapping[str, Any] | None) -> dict[str, object]:
    if report is None:
        return {
            "speech_count": None,
            "chunk_count": None,
            "queued_audio_seconds": None,
        }

    speech = _nested_mapping(report, "speech", report_kind="vad")
    chunks = _nested_mapping(report, "chunks", report_kind="vad")
    return {
        "speech_count": _required_nonnegative_int(
            speech.get("count"),
            report_kind="vad",
        ),
        "chunk_count": _required_nonnegative_int(
            chunks.get("count"),
            report_kind="vad",
        ),
        "queued_audio_seconds": _required_nonnegative_number(
            chunks.get("queued_audio_seconds"),
            report_kind="vad",
        ),
    }


def _stt_metadata(report: Mapping[str, Any] | None) -> dict[str, object]:
    if report is None:
        return {
            "segment_count": None,
            "elapsed_seconds": None,
            "real_time_factor": None,
        }

    transcript = _nested_mapping(report, "transcript", report_kind="benchmark")
    timing = _nested_mapping(report, "timing", report_kind="benchmark")
    return {
        "segment_count": _required_nonnegative_int(
            transcript.get("segment_count"),
            report_kind="benchmark",
        ),
        "elapsed_seconds": _required_nonnegative_number(
            timing.get("elapsed_seconds"),
            report_kind="benchmark",
        ),
        "real_time_factor": _optional_nonnegative_number(
            timing.get("real_time_factor"),
            report_kind="benchmark",
        ),
    }


def _nested_mapping(
    report: Mapping[str, Any],
    key: str,
    *,
    report_kind: str,
) -> Mapping[str, Any]:
    value = report.get(key)
    if not isinstance(value, Mapping):
        raise AudioEvidenceManifestError(
            f"audio evidence manifest {report_kind} report is invalid"
        )
    return value


def _required_nonnegative_int(value: object, *, report_kind: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise AudioEvidenceManifestError(
            f"audio evidence manifest {report_kind} report is invalid"
        )
    if value < 0:
        raise AudioEvidenceManifestError(
            f"audio evidence manifest {report_kind} report is invalid"
        )
    return value


def _required_nonnegative_number(value: object, *, report_kind: str) -> float:
    number = _number(value, report_kind=report_kind)
    if number < 0.0:
        raise AudioEvidenceManifestError(
            f"audio evidence manifest {report_kind} report is invalid"
        )
    return number


def _optional_nonnegative_number(
    value: object,
    *,
    report_kind: str,
) -> float | None:
    if value is None:
        return None
    return _required_nonnegative_number(value, report_kind=report_kind)


def _number(value: object, *, report_kind: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise AudioEvidenceManifestError(
            f"audio evidence manifest {report_kind} report is invalid"
        )
    number = float(value)
    if not math.isfinite(number):
        raise AudioEvidenceManifestError(
            f"audio evidence manifest {report_kind} report is invalid"
        )
    return number


def _optional_safe_status(value: object, *, report_kind: str) -> str | None:
    if value is None:
        return None
    if value not in {"available", "unavailable"}:
        raise AudioEvidenceManifestError(
            f"audio evidence manifest {report_kind} report is invalid"
        )
    return value


__all__ = [
    "ALLOWED_EVIDENCE_KINDS",
    "ALLOWED_SOURCE_METADATA_KEYS",
    "AudioEvidenceManifestError",
    "build_audio_evidence_manifest",
]
