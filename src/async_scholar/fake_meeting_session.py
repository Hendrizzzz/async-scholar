"""Synthetic meeting HTML-string inspection for local tests."""

from __future__ import annotations

from html.parser import HTMLParser
from typing import Any, Literal

from pydantic import VERSION, BaseModel, ValidationError

from async_scholar.fake_meeting import (
    FAKE_MEETING_FIXTURE_KIND,
    PARTICIPANT_COUNT_MAX,
    PARTICIPANT_NAME_MAX_LENGTH,
    _normalize_caption_status,
    _normalize_display_text,
    _normalize_fixture_id,
    _normalize_state,
)

if VERSION.startswith("2."):
    from pydantic import ConfigDict, field_validator

    _PYDANTIC_V2 = True
else:
    from pydantic import validator

    _PYDANTIC_V2 = False


FAKE_MEETING_SESSION_SNAPSHOT_KIND = "synthetic_fake_meeting_session"
FAKE_MEETING_SESSION_ERROR = "fake meeting session snapshot could not be built"
HTML_INPUT_MAX_LENGTH = 12_000
SAFE_FAKE_MEETING_SESSION_FIELDS = (
    "snapshot_kind",
    "fixture_id",
    "state",
    "caption_status",
    "participant_count",
    "participants",
)
_ACTIVE_ELEMENT_NAMES = frozenset(
    {
        "script",
        "iframe",
        "form",
        "input",
        "button",
        "textarea",
        "select",
        "option",
        "video",
        "canvas",
        "link",
        "img",
    }
)

FakeMeetingSessionSnapshotSummary = dict[str, str | int | tuple[str, ...]]


def _before_validator(*field_names: str) -> Any:
    if _PYDANTIC_V2:
        return field_validator(*field_names, mode="before")
    return validator(*field_names, pre=True, allow_reuse=True)


def _normalize_snapshot_participants(value: Any) -> tuple[str, ...]:
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


def _normalize_participant_count(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("participant_count is invalid")
    if value <= 0 or value > PARTICIPANT_COUNT_MAX:
        raise ValueError("participant_count is invalid")
    return value


class FakeMeetingSessionSnapshot(BaseModel):
    """Immutable synthetic session metadata parsed from local fixture HTML."""

    snapshot_kind: Literal["synthetic_fake_meeting_session"] = (
        FAKE_MEETING_SESSION_SNAPSHOT_KIND
    )
    fixture_id: str
    state: Literal["waiting", "live", "ended"]
    caption_status: Literal["disabled", "ready", "active"]
    participant_count: int
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

    @_before_validator("state")
    def _normalize_model_state(cls, value: Any) -> str:
        return _normalize_state(value)

    @_before_validator("caption_status")
    def _normalize_model_caption_status(cls, value: Any) -> str:
        return _normalize_caption_status(value)

    @_before_validator("participant_count")
    def _normalize_model_participant_count(cls, value: Any) -> int:
        return _normalize_participant_count(value)

    @_before_validator("participants")
    def _normalize_model_participants(cls, value: Any) -> tuple[str, ...]:
        return _normalize_snapshot_participants(value)

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if self.participant_count != len(self.participants):
            raise ValueError("participant_count is invalid")

    def to_json_ready(self) -> FakeMeetingSessionSnapshotSummary:
        """Return deterministic synthetic session metadata."""

        return _fake_meeting_session_snapshot_to_json_ready(
            _revalidate_fake_meeting_session_snapshot(self)
        )

    def to_safe_summary(self) -> FakeMeetingSessionSnapshotSummary:
        """Return deterministic metadata suitable for local test display."""

        return self.to_json_ready()

    def safe_summary(self) -> FakeMeetingSessionSnapshotSummary:
        """Alias for callers that need a concise safe display payload."""

        return self.to_json_ready()


class _SyntheticMeetingParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.fixture_attrs: dict[str, str] | None = None
        self.participants: list[str] = []
        self._failed = False

    @property
    def failed(self) -> bool:
        return self._failed

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        normalized_tag = tag.lower()
        attrs_dict = dict(attrs)
        if normalized_tag in _ACTIVE_ELEMENT_NAMES:
            self._failed = True
            return
        if any(name.lower().startswith("on") for name, _ in attrs):
            self._failed = True
            return
        if any(name.lower() in {"href", "src", "action"} for name, _ in attrs):
            self._failed = True
            return

        fixture_kind = attrs_dict.get("data-async-scholar-fixture-kind")
        if fixture_kind is not None:
            if self.fixture_attrs is not None:
                self._failed = True
                return
            self.fixture_attrs = {
                "fixture_kind": fixture_kind,
                "fixture_id": attrs_dict.get("data-async-scholar-fixture-id", ""),
                "state": attrs_dict.get("data-async-scholar-state", ""),
                "caption_status": attrs_dict.get(
                    "data-async-scholar-caption-status",
                    "",
                ),
                "participant_count": attrs_dict.get(
                    "data-async-scholar-participant-count",
                    "",
                ),
            }

        participant = attrs_dict.get("data-async-scholar-participant")
        if participant is not None:
            self.participants.append(participant)


def _model_to_primitive(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _revalidate_fake_meeting_session_snapshot(
    snapshot: FakeMeetingSessionSnapshot,
) -> FakeMeetingSessionSnapshot:
    if type(snapshot) is not FakeMeetingSessionSnapshot:
        raise ValueError(FAKE_MEETING_SESSION_ERROR)
    try:
        return FakeMeetingSessionSnapshot(**_model_to_primitive(snapshot))
    except (TypeError, ValidationError, ValueError):
        raise ValueError(FAKE_MEETING_SESSION_ERROR) from None


def _fake_meeting_session_snapshot_to_json_ready(
    snapshot: FakeMeetingSessionSnapshot,
) -> FakeMeetingSessionSnapshotSummary:
    return {
        "snapshot_kind": snapshot.snapshot_kind,
        "fixture_id": snapshot.fixture_id,
        "state": snapshot.state,
        "caption_status": snapshot.caption_status,
        "participant_count": snapshot.participant_count,
        "participants": snapshot.participants,
    }


def _normalize_html_input(value: Any) -> str:
    if type(value) is not str:
        raise ValueError(FAKE_MEETING_SESSION_ERROR)
    if not value or len(value) > HTML_INPUT_MAX_LENGTH:
        raise ValueError(FAKE_MEETING_SESSION_ERROR)
    return value


def _parse_count(value: str) -> int:
    if not value.isdecimal():
        raise ValueError(FAKE_MEETING_SESSION_ERROR)
    parsed = int(value)
    if parsed <= 0 or parsed > PARTICIPANT_COUNT_MAX:
        raise ValueError(FAKE_MEETING_SESSION_ERROR)
    return parsed


def inspect_fake_meeting_session_html(html_text: str) -> FakeMeetingSessionSnapshot:
    """Inspect synthetic fixture HTML already loaded in memory."""

    try:
        safe_html = _normalize_html_input(html_text)
        parser = _SyntheticMeetingParser()
        parser.feed(safe_html)
        parser.close()
        if parser.failed or parser.fixture_attrs is None:
            raise ValueError(FAKE_MEETING_SESSION_ERROR)

        attrs = parser.fixture_attrs
        if attrs["fixture_kind"] != FAKE_MEETING_FIXTURE_KIND:
            raise ValueError(FAKE_MEETING_SESSION_ERROR)
        participant_count = _parse_count(attrs["participant_count"])
        participants = _normalize_snapshot_participants(tuple(parser.participants))
        if participant_count != len(participants):
            raise ValueError(FAKE_MEETING_SESSION_ERROR)

        return FakeMeetingSessionSnapshot(
            fixture_id=attrs["fixture_id"],
            state=attrs["state"],
            caption_status=attrs["caption_status"],
            participant_count=participant_count,
            participants=participants,
        )
    except (TypeError, ValidationError, ValueError):
        raise ValueError(FAKE_MEETING_SESSION_ERROR) from None


def fake_meeting_session_snapshot_to_json_ready(
    snapshot: FakeMeetingSessionSnapshot,
) -> FakeMeetingSessionSnapshotSummary:
    """Return safe deterministic synthetic session metadata."""

    return _fake_meeting_session_snapshot_to_json_ready(
        _revalidate_fake_meeting_session_snapshot(snapshot)
    )


def fake_meeting_session_snapshot_safe_summary(
    snapshot: FakeMeetingSessionSnapshot,
) -> FakeMeetingSessionSnapshotSummary:
    """Return safe deterministic synthetic session metadata."""

    return _fake_meeting_session_snapshot_to_json_ready(
        _revalidate_fake_meeting_session_snapshot(snapshot)
    )
