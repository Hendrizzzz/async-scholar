"""Course metadata models for manually entered course details."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlsplit

from pydantic import VERSION, BaseModel, Field

if VERSION.startswith("2."):
    from pydantic import ConfigDict, field_validator

    _PYDANTIC_V2 = True
else:
    from pydantic import validator

    _PYDANTIC_V2 = False


COURSE_ID_MAX_LENGTH = 64
TITLE_MAX_LENGTH = 120
OPTIONAL_TEXT_MAX_LENGTH = 120
MEETING_URL_MAX_LENGTH = 2048

_COURSE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_ALLOWED_MEETING_SCHEMES = frozenset({"http", "https"})


def _before_validator(*field_names: str) -> Any:
    if _PYDANTIC_V2:
        return field_validator(*field_names, mode="before")
    return validator(*field_names, pre=True, allow_reuse=True)


def _clean_required_text(value: Any, *, field_name: str, max_length: int) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} is required")
    if len(normalized) > max_length:
        raise ValueError(f"{field_name} is too long")
    return normalized


def _clean_optional_text(value: Any, *, max_length: int) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("metadata text must be a string")

    normalized = value.strip()
    if not normalized:
        return None
    if len(normalized) > max_length:
        raise ValueError("metadata text is too long")
    return normalized


def _has_url_control_or_whitespace(value: str) -> bool:
    return any(
        char.isspace() or ord(char) < 0x20 or ord(char) == 0x7F for char in value
    )


class CourseMetadata(BaseModel):
    """Small immutable model for user-entered course metadata."""

    course_id: str
    title: str
    instructor_name: str | None = None
    meeting_url: str | None = Field(default=None, repr=False)
    meeting_label: str | None = None

    if _PYDANTIC_V2:
        model_config = ConfigDict(
            extra="forbid",
            frozen=True,
            hide_input_in_errors=True,
        )
    else:

        class Config:
            extra = "forbid"
            frozen = True

    @_before_validator("course_id")
    def _normalize_course_id(cls, value: Any) -> str:
        normalized = _clean_required_text(
            value,
            field_name="course_id",
            max_length=COURSE_ID_MAX_LENGTH,
        ).lower()
        if _COURSE_ID_PATTERN.fullmatch(normalized) is None:
            raise ValueError(
                "course_id must use letters, numbers, hyphens, or underscores"
            )
        return normalized

    @_before_validator("title")
    def _normalize_title(cls, value: Any) -> str:
        return _clean_required_text(
            value,
            field_name="title",
            max_length=TITLE_MAX_LENGTH,
        )

    @_before_validator("instructor_name", "meeting_label")
    def _normalize_optional_display_text(cls, value: Any) -> str | None:
        return _clean_optional_text(value, max_length=OPTIONAL_TEXT_MAX_LENGTH)

    @_before_validator("meeting_url")
    def _normalize_meeting_url(cls, value: Any) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("meeting link must be a string")

        normalized = value.strip()
        if not normalized:
            return None
        if len(normalized) > MEETING_URL_MAX_LENGTH:
            raise ValueError("meeting link is too long")
        if _has_url_control_or_whitespace(normalized):
            raise ValueError("meeting link contains unsupported characters")

        parsed = urlsplit(normalized)
        if parsed.scheme.lower() not in _ALLOWED_MEETING_SCHEMES or not parsed.netloc:
            raise ValueError("meeting link must use http:// or https://")
        return normalized

    def to_safe_summary(self) -> dict[str, str | None]:
        """Return non-sensitive metadata suitable for display or export."""

        return {
            "course_id": self.course_id,
            "title": self.title,
            "instructor_name": self.instructor_name,
            "meeting_label": self.meeting_label,
        }

    def safe_summary(self) -> dict[str, str | None]:
        """Alias for callers that need a concise safe display payload."""

        return self.to_safe_summary()
