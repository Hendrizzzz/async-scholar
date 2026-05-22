from __future__ import annotations

import json
from pathlib import Path

import pytest

from async_scholar.audio_evidence_manifest import (
    AudioEvidenceManifestError,
    build_audio_evidence_manifest,
)


def test_manifest_summarizes_only_allowlisted_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_audio = tmp_path / "private-token-meeting.wav"
    transcript_jsonl = tmp_path / "transcript-secret.jsonl"
    transcript_markdown = tmp_path / "transcript-secret.md"
    vad_report = tmp_path / "vad-plan-report.json"
    benchmark_report = tmp_path / "benchmark-report.json"
    source_audio.write_bytes(b"SECRET AUDIO TOKEN")
    transcript_jsonl.write_text("SECRET TRANSCRIPT TOKEN\n", encoding="utf-8")
    transcript_markdown.write_text("SECRET TRANSCRIPT TOKEN\n", encoding="utf-8")
    vad_report.write_text(
        json.dumps(
            {
                "speech": {"count": 32, "total_duration_seconds": 41.0},
                "chunks": {
                    "count": 6,
                    "queued_audio_seconds": 68.370375,
                    "timing_windows": [{"private": str(tmp_path / "token-window.wav")}],
                },
                "backpressure": {"recommended_action": "pause_file_input"},
            }
        ),
        encoding="utf-8",
    )
    benchmark_report.write_text(
        json.dumps(
            {
                "input": {
                    "audio_file_name": "private-token-meeting.wav",
                    "audio_duration_seconds": 68.370375,
                    "audio_duration_status": "available",
                },
                "model": {"reference": r"C:\Users\student\private-models\tiny"},
                "timing": {
                    "started_at_utc": "2026-05-23T00:00:00Z",
                    "elapsed_seconds": 4.515231,
                    "real_time_factor": 0.066041,
                    "notes": "SECRET BENCHMARK TOKEN",
                },
                "transcript": {
                    "session_id": "session-secret-token",
                    "segment_count": 16,
                },
                "artifacts": {
                    "transcript_jsonl": str(transcript_jsonl),
                    "transcript_markdown": str(transcript_markdown),
                },
            }
        ),
        encoding="utf-8",
    )
    original_open = Path.open
    protected_paths = {source_audio, transcript_jsonl, transcript_markdown}

    def guarded_open(path: Path, *args: object, **kwargs: object):
        if path in protected_paths:
            raise AssertionError("private artifact content was read")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)

    manifest = build_audio_evidence_manifest(
        evidence_kind="public_open_speech",
        source_label="Open Speech Repository Hindi sample",
        source_attribution="Open Speech Repository source identification required",
        source_metadata={
            "bit_depth": 16,
            "encoding": "PCM",
            "language": "Hindi",
            "sample_rate_hz": 16_000,
        },
        source_audio_path=source_audio,
        vad_report_path=vad_report,
        benchmark_report_path=benchmark_report,
        transcript_jsonl_path=transcript_jsonl,
        transcript_markdown_path=transcript_markdown,
    )

    assert manifest == {
        "schema_version": 1,
        "evidence_kind": "public_open_speech",
        "source": {
            "label": "Open Speech Repository Hindi sample",
            "attribution": "Open Speech Repository source identification required",
            "metadata": {
                "bit_depth": 16,
                "encoding": "PCM",
                "language": "Hindi",
                "sample_rate_hz": 16_000,
            },
        },
        "artifacts": {
            "source_audio_present": True,
            "vad_report_present": True,
            "benchmark_report_present": True,
            "transcript_jsonl_present": True,
            "transcript_markdown_present": True,
        },
        "audio": {
            "duration_seconds": 68.370375,
            "duration_status": "available",
        },
        "vad": {
            "speech_count": 32,
            "chunk_count": 6,
            "queued_audio_seconds": 68.370375,
        },
        "stt": {
            "segment_count": 16,
            "elapsed_seconds": 4.515231,
            "real_time_factor": 0.066041,
        },
    }
    manifest_text = json.dumps(manifest, sort_keys=True)
    for forbidden_fragment in (
        str(tmp_path),
        "private",
        "SECRET",
        "TOKEN",
        "meeting",
        "session-secret",
        "private-models",
        "timing_windows",
        "recommended_action",
        "started_at_utc",
        "notes",
        "audio_file_name",
        "transcript_secret",
    ):
        assert forbidden_fragment not in manifest_text


def test_manifest_marks_missing_optional_artifacts_without_parsing(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing-token-secret.json"

    manifest = build_audio_evidence_manifest(
        evidence_kind="synthetic_audio_fixture",
        source_label="Synthetic audio fixture",
        source_attribution="AsyncScholar local test fixture",
        source_metadata={"source_family": "synthetic_audio_fixture"},
        source_audio_path=missing,
        vad_report_path=missing,
        benchmark_report_path=missing,
        transcript_jsonl_path=missing,
        transcript_markdown_path=missing,
    )

    assert manifest["artifacts"] == {
        "source_audio_present": False,
        "vad_report_present": False,
        "benchmark_report_present": False,
        "transcript_jsonl_present": False,
        "transcript_markdown_present": False,
    }
    assert manifest["audio"] == {
        "duration_seconds": None,
        "duration_status": None,
    }
    assert manifest["vad"] == {
        "speech_count": None,
        "chunk_count": None,
        "queued_audio_seconds": None,
    }
    assert manifest["stt"] == {
        "segment_count": None,
        "elapsed_seconds": None,
        "real_time_factor": None,
    }
    assert str(tmp_path) not in json.dumps(manifest)


def test_malformed_reports_raise_sanitized_errors(tmp_path: Path) -> None:
    vad_report = tmp_path / "private-token-vad-report.json"
    vad_report.write_text(
        '{"speech": {"count": "SECRET TOKEN"',
        encoding="utf-8",
    )

    with pytest.raises(AudioEvidenceManifestError) as exc_info:
        build_audio_evidence_manifest(
            evidence_kind="public_open_speech",
            source_label="Open Speech Repository Hindi sample",
            source_attribution="Open Speech Repository source identification required",
            vad_report_path=vad_report,
        )

    assert str(exc_info.value) == (
        "audio evidence manifest vad report could not be parsed"
    )
    assert exc_info.value.__cause__ is None
    for forbidden_fragment in (str(tmp_path), "SECRET", "TOKEN", "private"):
        assert forbidden_fragment not in str(exc_info.value)


def test_invalid_report_scalars_raise_sanitized_errors(tmp_path: Path) -> None:
    benchmark_report = tmp_path / "benchmark-report.json"
    benchmark_report.write_text(
        json.dumps(
            {
                "input": {
                    "audio_duration_seconds": 1.0,
                    "audio_duration_status": "available",
                },
                "timing": {
                    "elapsed_seconds": "SECRET TOKEN",
                    "real_time_factor": 0.5,
                },
                "transcript": {"segment_count": 1},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(AudioEvidenceManifestError) as exc_info:
        build_audio_evidence_manifest(
            evidence_kind="public_open_speech",
            source_label="Open Speech Repository Hindi sample",
            source_attribution="Open Speech Repository source identification required",
            benchmark_report_path=benchmark_report,
        )

    assert str(exc_info.value) == (
        "audio evidence manifest benchmark report is invalid"
    )
    assert exc_info.value.__cause__ is None
    assert "SECRET" not in str(exc_info.value)
    assert "TOKEN" not in str(exc_info.value)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        (
            {"evidence_kind": "gate_d_pass"},
            "audio evidence manifest evidence kind is invalid",
        ),
        (
            {"source_label": r"C:\Users\student\secret"},
            "audio evidence manifest source label is invalid",
        ),
        (
            {"source_label": "CS101 class participant Alice"},
            "audio evidence manifest source label is invalid",
        ),
        (
            {"source_metadata": {"url": "https://example.test/private"}},
            "audio evidence manifest source metadata is invalid",
        ),
    ],
)
def test_unsafe_caller_metadata_is_rejected(
    kwargs: dict[str, object],
    message: str,
) -> None:
    call_kwargs: dict[str, object] = {
        "evidence_kind": "public_open_speech",
        "source_label": "Open Speech Repository Hindi sample",
        "source_attribution": "Open Speech Repository source identification required",
        "source_metadata": {"encoding": "PCM"},
    }
    call_kwargs.update(kwargs)

    with pytest.raises(AudioEvidenceManifestError) as exc_info:
        build_audio_evidence_manifest(**call_kwargs)

    assert str(exc_info.value) == message
