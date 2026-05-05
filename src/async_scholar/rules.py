"""Deterministic transcript-to-event rules for early fixture detection."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from async_scholar.schemas import LectureEvent, TranscriptSegment


@dataclass(frozen=True)
class _Rule:
    event_type: str
    patterns: tuple[re.Pattern[str], ...]
    confidence: float
    message: str


_ATTENDANCE_RULE = _Rule(
    event_type="attendance_prompt",
    patterns=(
        re.compile(r"\btake attendance\b", re.IGNORECASE),
        re.compile(r"\bcall (?:your|the) name\b", re.IGNORECASE),
        re.compile(r"\bplease say present\b", re.IGNORECASE),
        re.compile(r"\broll call\b", re.IGNORECASE),
        re.compile(r"\bmark (?:you|yourself) present\b", re.IGNORECASE),
    ),
    confidence=0.95,
    message="Attendance prompt detected.",
)

_RULES: tuple[_Rule, ...] = (
    _ATTENDANCE_RULE,
    _Rule(
        event_type="task_prompt",
        patterns=(
            re.compile(
                r"\bplease (?:submit|upload|complete|answer|respond)\b", re.IGNORECASE
            ),
            re.compile(
                r"\b(?:submit|upload|complete|answer) (?:the|your|a)\b", re.IGNORECASE
            ),
            re.compile(r"\b(?:work on|turn in) (?:the|your|a)\b", re.IGNORECASE),
            re.compile(
                r"\b(?:post|write) (?:your|a) (?:response|answer|reflection)\b",
                re.IGNORECASE,
            ),
        ),
        confidence=0.85,
        message="Task or action prompt detected.",
    ),
    _Rule(
        event_type="deadline_mention",
        patterns=(
            re.compile(
                r"\bdue (?:today|tomorrow|tonight|by|on|before|at)\b", re.IGNORECASE
            ),
            re.compile(r"\bdeadline\b", re.IGNORECASE),
            re.compile(r"\bbefore (?:midnight|class|next)\b", re.IGNORECASE),
            re.compile(r"\bby \d{1,2}(?::\d{2})?\s*(?:am|pm)\b", re.IGNORECASE),
        ),
        confidence=0.8,
        message="Deadline mention detected.",
    ),
    _Rule(
        event_type="dismissal_cue",
        patterns=(
            re.compile(r"\bclass (?:is )?(?:dismissed|over)\b", re.IGNORECASE),
            re.compile(r"\b(?:that'?s|that is) all for today\b", re.IGNORECASE),
            re.compile(r"\bwe'?ll stop here\b", re.IGNORECASE),
            re.compile(r"\bsee you (?:next time|tomorrow|on)\b", re.IGNORECASE),
            re.compile(r"\bend of class\b", re.IGNORECASE),
        ),
        confidence=0.9,
        message="Dismissal or end-of-class cue detected.",
    ),
)


def detect_events(segments: Iterable[TranscriptSegment]) -> list[LectureEvent]:
    """Detect lecture events from transcript segments using deterministic rules."""
    events: list[LectureEvent] = []

    for segment in segments:
        for rule in _RULES:
            if _matches(rule, segment.text):
                event_number = len(events) + 1
                events.append(
                    LectureEvent(
                        event_id=_event_id(
                            segment.session_id, event_number, rule.event_type
                        ),
                        session_id=segment.session_id,
                        event_type=rule.event_type,
                        detected_at_seconds=segment.start_seconds,
                        source_segment_ids=(segment.segment_id,),
                        message=rule.message,
                        confidence=rule.confidence,
                    )
                )

    return events


def _matches(rule: _Rule, text: str) -> bool:
    return any(pattern.search(text) for pattern in rule.patterns)


def _event_id(session_id: str, event_number: int, event_type: str) -> str:
    return f"{session_id}:event:{event_number:04d}:{event_type}"


__all__ = ["detect_events"]
