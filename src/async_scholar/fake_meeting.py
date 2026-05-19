"""Synthetic local meeting fixture contract."""

from __future__ import annotations

import html
import re
from typing import Any, Literal

from pydantic import VERSION, BaseModel, ValidationError

if VERSION.startswith("2."):
    from pydantic import ConfigDict, field_validator

    _PYDANTIC_V2 = True
else:
    from pydantic import validator

    _PYDANTIC_V2 = False


FAKE_MEETING_FIXTURE_KIND = "synthetic_fake_meeting"
FAKE_MEETING_ERROR = "fake meeting fixture could not be built"
FIXTURE_ID_MAX_LENGTH = 64
TITLE_MAX_LENGTH = 80
PARTICIPANT_NAME_MAX_LENGTH = 40
PARTICIPANT_COUNT_MAX = 12
MEETING_STATE_VALUES = ("waiting", "live", "ended")
CAPTION_STATUS_VALUES = ("disabled", "ready", "active")
SAFE_FAKE_MEETING_FIELDS = (
    "fixture_kind",
    "fixture_id",
    "title",
    "state",
    "caption_status",
    "participant_count",
    "participants",
)

_FIXTURE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_SAFE_DISPLAY_TEXT_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._-]{0,79}$")
_MEETING_STATE_SET = frozenset(MEETING_STATE_VALUES)
_CAPTION_STATUS_SET = frozenset(CAPTION_STATUS_VALUES)

FakeMeetingFixtureSummary = dict[str, str | int | tuple[str, ...]]


def _before_validator(*field_names: str) -> Any:
    if _PYDANTIC_V2:
        return field_validator(*field_names, mode="before")
    return validator(*field_names, pre=True, allow_reuse=True)


def _has_control_character(value: str) -> bool:
    return any(ord(char) < 0x20 or ord(char) == 0x7F for char in value)


def _normalize_fixture_id(value: Any) -> str:
    if type(value) is not str:
        raise ValueError("fixture_id is invalid")
    normalized = value.strip().lower()
    if normalized != value or not normalized:
        raise ValueError("fixture_id is invalid")
    if len(normalized) > FIXTURE_ID_MAX_LENGTH:
        raise ValueError("fixture_id is invalid")
    if _has_control_character(normalized):
        raise ValueError("fixture_id is invalid")
    if _FIXTURE_ID_PATTERN.fullmatch(normalized) is None:
        raise ValueError("fixture_id is invalid")
    return normalized


def _normalize_display_text(value: Any, *, field_name: str, max_length: int) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} is invalid")
    normalized = value.strip()
    if normalized != value or not normalized:
        raise ValueError(f"{field_name} is invalid")
    if len(normalized) > max_length:
        raise ValueError(f"{field_name} is invalid")
    if _has_control_character(normalized):
        raise ValueError(f"{field_name} is invalid")
    if _SAFE_DISPLAY_TEXT_PATTERN.fullmatch(normalized) is None:
        raise ValueError(f"{field_name} is invalid")
    if not normalized.startswith("Synthetic "):
        raise ValueError(f"{field_name} is invalid")
    return normalized


def _normalize_state(value: Any) -> str:
    if type(value) is not str:
        raise ValueError("state is invalid")
    normalized = value.strip().lower()
    if normalized != value:
        raise ValueError("state is invalid")
    if normalized not in _MEETING_STATE_SET:
        raise ValueError("state is invalid")
    return normalized


def _normalize_caption_status(value: Any) -> str:
    if type(value) is not str:
        raise ValueError("caption_status is invalid")
    normalized = value.strip().lower()
    if normalized != value:
        raise ValueError("caption_status is invalid")
    if normalized not in _CAPTION_STATUS_SET:
        raise ValueError("caption_status is invalid")
    return normalized


def _normalize_participants(value: Any) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("participants are invalid")
    if not value or len(value) > PARTICIPANT_COUNT_MAX:
        raise ValueError("participants are invalid")

    participants = tuple(
        _normalize_display_text(
            item,
            field_name="participant",
            max_length=PARTICIPANT_NAME_MAX_LENGTH,
        )
        for item in value
    )
    if len(set(participants)) != len(participants):
        raise ValueError("participants are invalid")
    return tuple(sorted(participants))


class FakeMeetingFixture(BaseModel):
    """Immutable synthetic meeting data for future local inspection tests."""

    fixture_kind: Literal["synthetic_fake_meeting"] = FAKE_MEETING_FIXTURE_KIND
    fixture_id: str
    title: str
    state: Literal["waiting", "live", "ended"]
    caption_status: Literal["disabled", "ready", "active"]
    participants: tuple[str, ...]

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

    @_before_validator("fixture_id")
    def _normalize_model_fixture_id(cls, value: Any) -> str:
        return _normalize_fixture_id(value)

    @_before_validator("title")
    def _normalize_model_title(cls, value: Any) -> str:
        return _normalize_display_text(
            value,
            field_name="title",
            max_length=TITLE_MAX_LENGTH,
        )

    @_before_validator("state")
    def _normalize_model_state(cls, value: Any) -> str:
        return _normalize_state(value)

    @_before_validator("caption_status")
    def _normalize_model_caption_status(cls, value: Any) -> str:
        return _normalize_caption_status(value)

    @_before_validator("participants")
    def _normalize_model_participants(cls, value: Any) -> tuple[str, ...]:
        return _normalize_participants(value)

    @property
    def participant_count(self) -> int:
        """Return the controlled synthetic participant count."""

        return len(self.participants)

    def to_json_ready(self) -> FakeMeetingFixtureSummary:
        """Return deterministic local-only fixture metadata."""

        return _fake_meeting_fixture_to_json_ready(_revalidate_fake_meeting(self))

    def to_safe_summary(self) -> FakeMeetingFixtureSummary:
        """Return deterministic metadata suitable for local test display."""

        return self.to_json_ready()

    def safe_summary(self) -> FakeMeetingFixtureSummary:
        """Alias for callers that need a concise safe display payload."""

        return self.to_json_ready()

    def to_html_document(self) -> str:
        """Render inert local HTML for future fixture inspection."""

        return fake_meeting_fixture_to_html(self)


def _model_to_primitive(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _revalidate_fake_meeting(fixture: FakeMeetingFixture) -> FakeMeetingFixture:
    if type(fixture) is not FakeMeetingFixture:
        raise ValueError(FAKE_MEETING_ERROR)
    try:
        return FakeMeetingFixture(**_model_to_primitive(fixture))
    except (TypeError, ValidationError, ValueError):
        raise ValueError(FAKE_MEETING_ERROR) from None


def _fake_meeting_fixture_to_json_ready(
    fixture: FakeMeetingFixture,
) -> FakeMeetingFixtureSummary:
    return {
        "fixture_kind": fixture.fixture_kind,
        "fixture_id": fixture.fixture_id,
        "title": fixture.title,
        "state": fixture.state,
        "caption_status": fixture.caption_status,
        "participant_count": fixture.participant_count,
        "participants": fixture.participants,
    }


def _escape_attribute(value: str) -> str:
    return html.escape(value, quote=True)


def _escape_text(value: str) -> str:
    return html.escape(value, quote=False)


def build_fake_meeting_fixture(
    *,
    fixture_id: str = "alpha_fixture",
    title: str = "Synthetic Seminar",
    state: str = "live",
    caption_status: str = "ready",
    participants: tuple[str, ...] | list[str] = (
        "Synthetic Instructor",
        "Synthetic Learner",
    ),
) -> FakeMeetingFixture:
    """Build deterministic synthetic meeting metadata with no runtime behavior."""

    try:
        return FakeMeetingFixture(
            fixture_id=fixture_id,
            title=title,
            state=state,
            caption_status=caption_status,
            participants=participants,
        )
    except (TypeError, ValidationError, ValueError):
        raise ValueError(FAKE_MEETING_ERROR) from None


def fake_meeting_fixture_to_json_ready(
    fixture: FakeMeetingFixture,
) -> FakeMeetingFixtureSummary:
    """Return safe deterministic fake-meeting metadata."""

    return _fake_meeting_fixture_to_json_ready(_revalidate_fake_meeting(fixture))


def fake_meeting_fixture_safe_summary(
    fixture: FakeMeetingFixture,
) -> FakeMeetingFixtureSummary:
    """Return safe deterministic fake-meeting metadata."""

    return _fake_meeting_fixture_to_json_ready(_revalidate_fake_meeting(fixture))


def fake_meeting_fixture_to_html(fixture: FakeMeetingFixture) -> str:
    """Render an inert synthetic meeting fixture as deterministic HTML."""

    safe_fixture = _revalidate_fake_meeting(fixture)
    participants_html = "\n".join(
        (
            '      <li class="participant" data-async-scholar-participant='
            f'"{_escape_attribute(participant)}">{_escape_text(participant)}</li>'
        )
        for participant in safe_fixture.participants
    )
    return "\n".join(
        (
            "<!doctype html>",
            '<html lang="en">',
            "  <head>",
            '    <meta charset="utf-8">',
            f"    <title>{_escape_text(safe_fixture.title)}</title>",
            "  </head>",
            (
                "  <body data-async-scholar-fixture-kind="
                f'"{safe_fixture.fixture_kind}"'
                f' data-async-scholar-fixture-id="{safe_fixture.fixture_id}"'
                f' data-async-scholar-state="{safe_fixture.state}"'
                f' data-async-scholar-caption-status="{safe_fixture.caption_status}"'
                f' data-async-scholar-participant-count="'
                f'{safe_fixture.participant_count}">'
            ),
            '    <main id="synthetic-meeting-root">',
            (
                '      <section aria-label="Synthetic meeting status"'
                ' data-async-scholar-session-awareness="synthetic-local-only">'
            ),
            f"        <h1>{_escape_text(safe_fixture.title)}</h1>",
            (f"        <p data-async-scholar-meeting-state>{safe_fixture.state}</p>"),
            (
                "        <p data-async-scholar-caption-state>"
                f"{safe_fixture.caption_status}</p>"
            ),
            "      </section>",
            '      <ul aria-label="Synthetic participants">',
            participants_html,
            "      </ul>",
            "    </main>",
            "  </body>",
            "</html>",
        )
    )
