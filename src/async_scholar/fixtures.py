"""Helpers for loading synthetic transcript fixtures."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from async_scholar.schemas import TranscriptSegment

_REQUIRED_FIXTURE_FIELDS = frozenset({"start_s", "end_s", "text"})
_ALLOWED_FIXTURE_FIELDS = _REQUIRED_FIXTURE_FIELDS | {"speaker"}


def load_transcript_fixture(path: str | Path) -> list[TranscriptSegment]:
    """Load a transcript JSONL fixture into validated transcript segments."""
    fixture_path = Path(path)
    session_id = f"fixture:{fixture_path.stem}"
    segments: list[TranscriptSegment] = []

    with fixture_path.open(encoding="utf-8") as fixture_file:
        for line_number, line in enumerate(fixture_file, start=1):
            stripped = line.strip()
            if not stripped:
                continue

            record = _parse_jsonl_record(fixture_path, line_number, stripped)
            segment_number = len(segments) + 1
            model_data = _build_segment_data(
                fixture_path=fixture_path,
                line_number=line_number,
                record=record,
                session_id=session_id,
                segment_number=segment_number,
            )
            segments.append(_validate_segment(fixture_path, line_number, model_data))

    return segments


def _parse_jsonl_record(
    fixture_path: Path, line_number: int, line: str
) -> dict[str, object]:
    try:
        record = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Malformed JSONL in {fixture_path} on line {line_number}: {exc.msg}"
        ) from exc

    if not isinstance(record, dict):
        raise ValueError(
            f"Invalid transcript fixture record in {fixture_path} on line "
            f"{line_number}: expected a JSON object"
        )

    return record


def _build_segment_data(
    *,
    fixture_path: Path,
    line_number: int,
    record: dict[str, object],
    session_id: str,
    segment_number: int,
) -> dict[str, object]:
    missing_fields = _REQUIRED_FIXTURE_FIELDS - record.keys()
    extra_fields = record.keys() - _ALLOWED_FIXTURE_FIELDS

    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(
            f"Invalid transcript fixture record in {fixture_path} on line "
            f"{line_number}: missing required field(s): {missing}"
        )

    if extra_fields:
        extra = ", ".join(sorted(extra_fields))
        raise ValueError(
            f"Invalid transcript fixture record in {fixture_path} on line "
            f"{line_number}: unexpected field(s): {extra}"
        )

    return {
        "segment_id": f"{session_id}:segment:{segment_number:04d}",
        "session_id": session_id,
        "start_seconds": record["start_s"],
        "end_seconds": record["end_s"],
        "text": record["text"],
        "speaker": record.get("speaker"),
    }


def _validate_segment(
    fixture_path: Path, line_number: int, model_data: dict[str, object]
) -> TranscriptSegment:
    try:
        return TranscriptSegment(**model_data)
    except ValidationError as exc:
        raise ValueError(
            f"Invalid transcript fixture record in {fixture_path} on line "
            f"{line_number}: {exc.errors()[0]['msg']}"
        ) from exc
