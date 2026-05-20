"""Local file artifacts for detected lecture events."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from async_scholar.alert_dispatch import (
    build_urgent_alert_retry_log_decisions,
    dispatch_alert,
)
from async_scholar.schemas import Alert, LectureEvent, TranscriptSegment

_SAFE_SESSION_ID_PATTERN = re.compile(r"[^A-Za-z0-9_-]+")
_MAX_REVIEWER_SNIPPET_CHARS = 220
_FILE_ALERT_PROVIDER = "file"
_ALERT_LOG_SESSION_ID = "alert-log-session"
_ALERT_LOG_GENERIC_EVENT_TYPE = "lecture_event"
_SYNTHETIC_SESSION_AWARENESS_EVENT_TYPE = "synthetic_session_awareness"
_SYNTHETIC_SESSION_AWARENESS_ALERT_MESSAGE = "Synthetic session awareness recorded."
_SYNTHETIC_SESSION_AWARENESS_REVIEWER_SESSION_ID = "synthetic-session"
_ALERT_LOG_EVENT_MESSAGES = {
    "attendance_prompt": "Attendance prompt detected.",
    "camera_mic_request": "Camera or micro" + "phone request detected.",
    "deadline_mention": "Deadline mention detected.",
    "direct_question": "Direct question detected.",
    "dismissal_cue": "Dismissal cue detected.",
    "name_call": "Name call detected.",
    "quiz_prompt": "Quiz prompt detected.",
    "task_prompt": "Task prompt detected.",
    _SYNTHETIC_SESSION_AWARENESS_EVENT_TYPE: (
        _SYNTHETIC_SESSION_AWARENESS_ALERT_MESSAGE
    ),
    _ALERT_LOG_GENERIC_EVENT_TYPE: "Lecture event detected.",
}


@dataclass(frozen=True)
class ArtifactPaths:
    output_dir: Path
    events_path: Path
    alerts_path: Path
    reviewer_path: Path


@dataclass(frozen=True)
class TranscriptArtifactPaths:
    output_dir: Path
    transcript_jsonl_path: Path
    transcript_markdown_path: Path


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


def write_transcript_artifacts(
    *,
    session_id: str,
    segments: Iterable[TranscriptSegment],
    output_root: str | Path,
) -> TranscriptArtifactPaths:
    """Write canonical and readable transcript artifacts for one session."""
    segment_list = list(segments)
    output_dir = Path(output_root) / safe_session_id(session_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    return TranscriptArtifactPaths(
        output_dir=output_dir,
        transcript_jsonl_path=write_transcript_jsonl(segment_list, output_dir),
        transcript_markdown_path=write_transcript_markdown(
            session_id=session_id,
            segments=segment_list,
            output_dir=output_dir,
        ),
    )


def write_transcript_jsonl(
    segments: Iterable[TranscriptSegment],
    output_dir: str | Path,
) -> Path:
    """Write transcript segments as canonical JSONL, one segment per line."""
    transcript_path = Path(output_dir) / "transcript.jsonl"
    with transcript_path.open("w", encoding="utf-8", newline="\n") as transcript_file:
        for segment in segments:
            transcript_file.write(_to_json_line(segment.model_dump(mode="json")))
    return transcript_path


def write_transcript_markdown(
    *,
    session_id: str,
    segments: Iterable[TranscriptSegment],
    output_dir: str | Path,
) -> Path:
    """Write a readable transcript Markdown file in segment order."""
    segment_list = list(segments)
    lines = [
        "# AsyncScholar Transcript",
        "",
        f"Session: `{session_id}`",
        f"Segments: {len(segment_list)}",
        "",
    ]

    if not segment_list:
        lines.append("No transcript segments.")
    else:
        for segment in segment_list:
            lines.extend(_transcript_segment_lines(segment))

    transcript_path = Path(output_dir) / "transcript.md"
    transcript_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return transcript_path


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
        for alert_index, event in enumerate(events, start=1):
            alert_event_type = _sanitize_alert_log_event_type(event.event_type)
            dispatch_results = dispatch_alert(
                event,
                provider_names=(_FILE_ALERT_PROVIDER,),
                dispatchers={_FILE_ALERT_PROVIDER: _record_file_alert_dispatch},
            )
            alert = Alert(
                alert_id=f"alert-log-alert-{alert_index:04d}",
                session_id=_ALERT_LOG_SESSION_ID,
                event_id=f"alert-log-event-{alert_index:04d}",
                message=_alert_log_message(alert_event_type),
                created_at=alert_time,
            )
            payload = alert.model_dump(mode="json") | {
                "event_type": alert_event_type,
                "severity": dispatch_results[0]["severity"],
                "dispatch_results": dispatch_results,
                "retry_log_decisions": build_urgent_alert_retry_log_decisions(
                    dispatch_results
                ),
            }
            alerts_file.write(_to_json_line(payload))

    return alerts_path


def _record_file_alert_dispatch(_payload: object) -> None:
    return None


def _sanitize_alert_log_event_type(event_type: str) -> str:
    if event_type in _ALERT_LOG_EVENT_MESSAGES:
        return event_type
    return _ALERT_LOG_GENERIC_EVENT_TYPE


def _alert_log_message(event_type: str) -> str:
    return _ALERT_LOG_EVENT_MESSAGES.get(
        event_type,
        _ALERT_LOG_EVENT_MESSAGES[_ALERT_LOG_GENERIC_EVENT_TYPE],
    )


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
    if event.event_type == _SYNTHETIC_SESSION_AWARENESS_EVENT_TYPE:
        return _synthetic_session_awareness_reviewer_lines(event)

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


def _synthetic_session_awareness_reviewer_lines(event: LectureEvent) -> list[str]:
    return [
        "## Synthetic Session Awareness",
        "",
        f"- Time: {event.detected_at_seconds:g}s",
        f"- Event: {_SYNTHETIC_SESSION_AWARENESS_ALERT_MESSAGE}",
        f"- Confidence: {event.confidence:.2f}",
        "- Evidence: Synthetic session metadata only.",
        "",
    ]


def _format_snippet(segment: TranscriptSegment) -> str:
    speaker = f"{segment.speaker}: " if segment.speaker else ""
    return f"{speaker}{_clip_snippet(segment.text)}"


def _transcript_segment_lines(segment: TranscriptSegment) -> list[str]:
    lines = [
        f"## {_format_time_range(segment)}",
        "",
    ]
    if segment.speaker:
        lines.append(f"**{segment.speaker}:** {segment.text}")
    else:
        lines.append(segment.text)

    lines.append("")
    return lines


def _format_time_range(segment: TranscriptSegment) -> str:
    return f"{segment.start_seconds:g}s - {segment.end_seconds:g}s"


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
        if events[0].event_type == _SYNTHETIC_SESSION_AWARENESS_EVENT_TYPE:
            return _SYNTHETIC_SESSION_AWARENESS_REVIEWER_SESSION_ID
        return events[0].session_id

    first_segment = next(iter(segments), None)
    if first_segment is not None:
        return first_segment.session_id

    return "unknown"


def _to_json_line(payload: dict[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"


__all__ = [
    "ArtifactPaths",
    "TranscriptArtifactPaths",
    "safe_session_id",
    "write_alert_log",
    "write_events_jsonl",
    "write_reviewer_markdown",
    "write_session_artifacts",
    "write_transcript_artifacts",
    "write_transcript_jsonl",
    "write_transcript_markdown",
]
