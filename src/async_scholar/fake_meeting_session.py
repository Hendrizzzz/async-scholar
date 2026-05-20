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
FAKE_MEETING_SESSION_HISTORY_KIND = "synthetic_fake_meeting_session_history"
FAKE_MEETING_SESSION_ERROR = "fake meeting session snapshot could not be built"
FAKE_MEETING_SESSION_HISTORY_ERROR = (
    "fake meeting session history summary could not be built"
)
HTML_INPUT_MAX_LENGTH = 12_000
SESSION_HISTORY_MAX_SNAPSHOTS = 12
SAFE_FAKE_MEETING_SESSION_FIELDS = (
    "snapshot_kind",
    "fixture_id",
    "state",
    "caption_status",
    "participant_count",
    "participants",
)
SAFE_FAKE_MEETING_SESSION_HISTORY_FIELDS = (
    "history_kind",
    "fixture_id",
    "snapshot_count",
    "ordered_states",
    "ordered_caption_statuses",
    "ordered_participant_counts",
    "final_state",
    "final_caption_status",
    "max_participant_count",
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
FakeMeetingSessionHistorySummary = dict[
    str,
    int | str | tuple[int, ...] | tuple[str, ...],
]


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


def _normalize_snapshot_history(value: Any) -> tuple[FakeMeetingSessionSnapshot, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple)):
        raise ValueError(FAKE_MEETING_SESSION_HISTORY_ERROR)
    if not value or len(value) > SESSION_HISTORY_MAX_SNAPSHOTS:
        raise ValueError(FAKE_MEETING_SESSION_HISTORY_ERROR)

    snapshots = tuple(_revalidate_fake_meeting_session_snapshot(item) for item in value)
    fixture_id = snapshots[0].fixture_id
    if any(snapshot.fixture_id != fixture_id for snapshot in snapshots):
        raise ValueError(FAKE_MEETING_SESSION_HISTORY_ERROR)
    return snapshots


def _fake_meeting_session_history_to_safe_summary(
    snapshots: tuple[FakeMeetingSessionSnapshot, ...],
) -> FakeMeetingSessionHistorySummary:
    participants = tuple(
        sorted(
            {
                participant
                for snapshot in snapshots
                for participant in snapshot.participants
            }
        )
    )
    participant_counts = tuple(snapshot.participant_count for snapshot in snapshots)

    return {
        "history_kind": FAKE_MEETING_SESSION_HISTORY_KIND,
        "fixture_id": snapshots[0].fixture_id,
        "snapshot_count": len(snapshots),
        "ordered_states": tuple(snapshot.state for snapshot in snapshots),
        "ordered_caption_statuses": tuple(
            snapshot.caption_status for snapshot in snapshots
        ),
        "ordered_participant_counts": participant_counts,
        "final_state": snapshots[-1].state,
        "final_caption_status": snapshots[-1].caption_status,
        "max_participant_count": max(participant_counts),
        "participants": participants,
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


def build_fake_meeting_session_history_summary(
    snapshots: object,
) -> FakeMeetingSessionHistorySummary:
    """Return a bounded safe summary for synthetic session snapshots."""

    try:
        safe_snapshots = _normalize_snapshot_history(snapshots)
        return _fake_meeting_session_history_to_safe_summary(safe_snapshots)
    except (TypeError, ValidationError, ValueError):
        raise ValueError(FAKE_MEETING_SESSION_HISTORY_ERROR) from None
