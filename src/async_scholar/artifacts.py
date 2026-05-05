"""Local file artifacts for detected lecture events."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from async_scholar.schemas import Alert, LectureEvent, TranscriptSegment

_SAFE_SESSION_ID_PATTERN = re.compile(r"[^A-Za-z0-9_-]+")
_MAX_REVIEWER_SNIPPET_CHARS = 220


@dataclass(frozen=True)
class ArtifactPaths:
    output_dir: Path
    events_path: Path
    alerts_path: Path
    reviewer_path: Path


def safe_session_id(session_id: str) -> str:
    """Convert a validated session ID into a filesystem-safe directory name."""
    safe_id = _SAFE_SESSION_ID_PATTERN.sub("_", session_id).strip("_")
    return safe_id or "session"


def write_session_artifacts(
    *,
    session_id: str,
    segments: Sequence[TranscriptSegment],
    events: Sequence[LectureEvent],
    output_root: str | Path,
    created_at: datetime | None = None,
) -> ArtifactPaths:
    output_dir = Path(output_root) / safe_session_id(session_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    return ArtifactPaths(
        output_dir=output_dir,
        events_path=write_events_jsonl(events, output_dir),
        alerts_path=write_alert_log(events, output_dir, created_at=created_at),
        reviewer_path=write_reviewer_markdown(events, segments, output_dir),
    )


def write_events_jsonl(
    events: Iterable[LectureEvent],
    output_dir: str | Path,
) -> Path:
    """Write detected events as canonical JSONL, one event per line."""
    events_path = Path(output_dir) / "events.jsonl"
    with events_path.open("w", encoding="utf-8", newline="\n") as events_file:
        for event in events:
            events_file.write(_to_json_line(event.model_dump(mode="json")))
    return events_path


def write_alert_log(
    events: Iterable[LectureEvent],
    output_dir: str | Path,
    *,
    created_at: datetime | None = None,
) -> Path:
    """Write fake file alerts without copying transcript text into the log."""
    alert_time = created_at or datetime.now(UTC)
    alerts_path = Path(output_dir) / "alerts.log"

    with alerts_path.open("w", encoding="utf-8", newline="\n") as alerts_file:
        for event in events:
            alert = Alert(
                alert_id=f"{event.event_id}:alert",
                session_id=event.session_id,
                event_id=event.event_id,
                message=event.message,
                created_at=alert_time,
            )
            payload = alert.model_dump(mode="json") | {"event_type": event.event_type}
            alerts_file.write(_to_json_line(payload))

    return alerts_path


def write_reviewer_markdown(
    events: Iterable[LectureEvent],
    segments: Iterable[TranscriptSegment],
    output_dir: str | Path,
) -> Path:
    """Write an extractive reviewer from detected events and source snippets."""
    event_list = list(events)
    segment_by_id = {segment.segment_id: segment for segment in segments}
    session_id = _reviewer_session_id(event_list, segment_by_id.values())

    lines = [
        "# AsyncScholar Reviewer",
        "",
        f"Session: `{session_id}`",
        f"Detected events: {len(event_list)}",
        "",
    ]

    if not event_list:
        lines.append("No detected events.")
    else:
        for event in event_list:
            lines.extend(_reviewer_event_lines(event, segment_by_id))

    reviewer_path = Path(output_dir) / "reviewer.md"
    reviewer_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return reviewer_path


def _reviewer_event_lines(
    event: LectureEvent,
    segment_by_id: dict[str, TranscriptSegment],
) -> list[str]:
    label = event.event_type.replace("_", " ").title()
    lines = [
        f"## {label}",
        "",
        f"- Time: {event.detected_at_seconds:g}s",
        f"- Event: {event.message}",
        f"- Confidence: {event.confidence:.2f}",
        f"- Source segment IDs: {', '.join(event.source_segment_ids)}",
        "- Source snippets:",
    ]

    for segment_id in event.source_segment_ids:
        segment = segment_by_id.get(segment_id)
        if segment is None:
            lines.append(f"  > Missing transcript segment: {segment_id}")
            continue
        lines.append(f"  > {_format_snippet(segment)}")

    lines.append("")
    return lines


def _format_snippet(segment: TranscriptSegment) -> str:
    speaker = f"{segment.speaker}: " if segment.speaker else ""
    return f"{speaker}{_clip_snippet(segment.text)}"


def _clip_snippet(text: str) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= _MAX_REVIEWER_SNIPPET_CHARS:
        return normalized
    return f"{normalized[: _MAX_REVIEWER_SNIPPET_CHARS - 3].rstrip()}..."


def _reviewer_session_id(
    events: Sequence[LectureEvent],
    segments: Iterable[TranscriptSegment],
) -> str:
    if events:
        return events[0].session_id

    first_segment = next(iter(segments), None)
    if first_segment is not None:
        return first_segment.session_id

    return "unknown"


def _to_json_line(payload: dict[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"


__all__ = [
    "ArtifactPaths",
    "safe_session_id",
    "write_alert_log",
    "write_events_jsonl",
    "write_reviewer_markdown",
    "write_session_artifacts",
]
