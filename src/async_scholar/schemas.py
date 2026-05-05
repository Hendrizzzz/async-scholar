"""Shared data schemas for AsyncScholar's early pipeline."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

AlertStatus = Literal["pending", "sent", "acknowledged"]


def _require_non_blank(value: str | None) -> str | None:
    if value is not None and not value:
        raise ValueError("must not be blank")
    return value


class SchemaModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )


class TranscriptSegment(SchemaModel):
    segment_id: str
    session_id: str
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    text: str
    speaker: str | None = None

    @field_validator("segment_id", "session_id", "text", "speaker")
    @classmethod
    def fields_must_not_be_blank(cls, value: str | None) -> str | None:
        return _require_non_blank(value)

    @model_validator(mode="after")
    def end_must_follow_start(self) -> Self:
        if self.end_seconds <= self.start_seconds:
            raise ValueError("end_seconds must be greater than start_seconds")
        return self


class LectureEvent(SchemaModel):
    event_id: str
    session_id: str
    event_type: str
    detected_at_seconds: float = Field(ge=0)
    source_segment_ids: tuple[str, ...] = Field(min_length=1)
    message: str
    confidence: float = Field(default=1.0, ge=0, le=1)

    @field_validator("event_id", "session_id", "event_type", "message")
    @classmethod
    def fields_must_not_be_blank(cls, value: str) -> str:
        return _require_non_blank(value)

    @field_validator("source_segment_ids")
    @classmethod
    def source_segment_ids_must_not_be_blank(
        cls,
        value: tuple[str, ...],
    ) -> tuple[str, ...]:
        if any(not segment_id for segment_id in value):
            raise ValueError("source_segment_ids must not contain blank values")
        return value


class Alert(SchemaModel):
    alert_id: str
    session_id: str
    event_id: str
    message: str
    created_at: datetime
    requires_confirmation: bool = True
    status: AlertStatus = "pending"

    @field_validator("alert_id", "session_id", "event_id", "message")
    @classmethod
    def fields_must_not_be_blank(cls, value: str) -> str:
        return _require_non_blank(value)


class SessionMetadata(SchemaModel):
    session_id: str
    course_id: str
    course_title: str
    started_at: datetime
    ended_at: datetime | None = None

    @field_validator("session_id", "course_id", "course_title")
    @classmethod
    def fields_must_not_be_blank(cls, value: str) -> str:
        return _require_non_blank(value)

    @model_validator(mode="after")
    def end_must_not_precede_start(self) -> Self:
        if self.ended_at is not None and self.ended_at < self.started_at:
            raise ValueError("ended_at must not be before started_at")
        return self


__all__ = [
    "Alert",
    "AlertStatus",
    "LectureEvent",
    "SessionMetadata",
    "TranscriptSegment",
]
