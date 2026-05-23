from __future__ import annotations

import inspect
from collections.abc import Sequence
from pathlib import Path

import pytest

from async_scholar import (
    session_window_recovery_batch_review as recovery_batch_review,
)
from async_scholar.session_window_recovery_batch_review import (
    STORED_SESSION_WINDOW_RECOVERY_REVIEW_BATCH_ERROR,
    build_stored_session_window_recovery_review_batch,
)

BATCH_KEYS = (
    "batch_kind",
    "review_count",
    "manual_review_required_count",
    "not_required_count",
    "required_count",
    "reviews",
)
REVIEW_KEYS = (
    "review_kind",
    "session_id",
    "runtime_lifecycle_status",
    "archive_recovery_status",
    "archive_existing_count",
    "archive_missing_count",
    "recovery_decision",
    "manual_review_required",
    "review_status",
    "review_reason",
    "safe_next_review_action",
)


def _review(session_id: str, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "review_kind": "stored_session_window_recovery_review",
        "session_id": session_id,
        "runtime_lifecycle_status": "not_started",
        "archive_recovery_status": "empty",
        "archive_existing_count": 0,
        "archive_missing_count": 6,
        "recovery_decision": "no_action",
        "manual_review_required": False,
        "review_status": "not_required",
        "review_reason": "none",
        "safe_next_review_action": "leave_archive_unchanged",
    }
    payload.update(overrides)
    return payload


class _SpoofedStringLike:
    def __init__(self, equal_to: str) -> None:
        self.equal_to = equal_to

    def __eq__(self, other: object) -> bool:
        return other == self.equal_to


class _SpoofedStr(str):
    def __new__(cls, value: str, equal_to: str) -> _SpoofedStr:
        instance = str.__new__(cls, value)
        instance.equal_to = equal_to
        return instance

    def __eq__(self, other: object) -> bool:
        return other == self.equal_to

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.equal_to)


class _LyingLongSessionIdSequence(Sequence[str]):
    def __init__(self) -> None:
        self._values = tuple(f"session-{index:03d}" for index in range(26))

    def __len__(self) -> int:
        return 1

    def __getitem__(self, index: int) -> str:
        return self._values[index]


def _assert_batch_error(archive_root: object, session_ids: object) -> None:
    with pytest.raises(ValueError) as exc_info:
        build_stored_session_window_recovery_review_batch(
            archive_root,  # type: ignore[arg-type]
            session_ids,  # type: ignore[arg-type]
        )
    assert str(exc_info.value) == STORED_SESSION_WINDOW_RECOVERY_REVIEW_BATCH_ERROR


def test_build_recovery_review_batch_mixed_reviews_preserves_input_order(
    monkeypatch,
) -> None:
    delegated_session_ids: list[str] = []
    reviews = {
        "session-001": _review("session-001"),
        "session-002": _review(
            "session-002",
            runtime_lifecycle_status="started",
            recovery_decision="inspect_active_session",
            manual_review_required=True,
            review_status="required",
            review_reason="active_session_runtime",
            safe_next_review_action="inspect_runtime_metadata",
        ),
        "session-003": _review(
            "session-003",
            archive_recovery_status="partial",
            archive_existing_count=1,
            archive_missing_count=5,
            recovery_decision="inspect_partial_archive",
            manual_review_required=True,
            review_status="required",
            review_reason="partial_archive_metadata",
            safe_next_review_action="inspect_archive_metadata",
        ),
    }

    def fake_build(archive_root: Path, session_id: str) -> dict[str, object]:
        assert archive_root == Path("archive-root")
        delegated_session_ids.append(session_id)
        return reviews[session_id]

    monkeypatch.setattr(
        recovery_batch_review,
        "build_stored_session_window_recovery_review",
        fake_build,
    )

    batch = build_stored_session_window_recovery_review_batch(
        Path("archive-root"),
        ("session-002", "session-001", "session-003"),
    )

    assert tuple(batch) == BATCH_KEYS
    assert batch == {
        "batch_kind": "stored_session_window_recovery_review_batch",
        "review_count": 3,
        "manual_review_required_count": 2,
        "not_required_count": 1,
        "required_count": 2,
        "reviews": [
            reviews["session-002"],
            reviews["session-001"],
            reviews["session-003"],
        ],
    }
    assert delegated_session_ids == ["session-002", "session-001", "session-003"]


def test_build_recovery_review_batch_is_deterministic(monkeypatch) -> None:
    monkeypatch.setattr(
        recovery_batch_review,
        "build_stored_session_window_recovery_review",
        lambda archive_root, session_id: _review(session_id),
    )

    first = build_stored_session_window_recovery_review_batch(
        Path("archive-root"),
        ("session-001", "session-002"),
    )
    second = build_stored_session_window_recovery_review_batch(
        Path("archive-root"),
        ("session-001", "session-002"),
    )

    assert first == second
    assert [review["session_id"] for review in first["reviews"]] == [
        "session-001",
        "session-002",
    ]


@pytest.mark.parametrize(
    "session_ids",
    (
        pytest.param("session-001", id="bare-string"),
        pytest.param(b"session-001", id="bare-bytes"),
        pytest.param((), id="empty"),
        pytest.param(["session-001", "session-001"], id="duplicate"),
        pytest.param(["session-001", 123], id="non-string"),
        pytest.param(["session-001", "../private"], id="unsafe"),
        pytest.param(tuple(f"session-{index:03d}" for index in range(26)), id="large"),
        pytest.param((f"session-{index:03d}" for index in range(2)), id="generator"),
        pytest.param(_LyingLongSessionIdSequence(), id="lying-long-sequence"),
    ),
)
def test_build_recovery_review_batch_rejects_invalid_sequences_before_delegation(
    monkeypatch,
    session_ids: object,
) -> None:
    delegated_session_ids: list[str] = []

    def fake_build(archive_root: Path, session_id: str) -> dict[str, object]:
        delegated_session_ids.append(session_id)
        return _review(session_id)

    monkeypatch.setattr(
        recovery_batch_review,
        "build_stored_session_window_recovery_review",
        fake_build,
    )

    _assert_batch_error(Path("archive-root"), session_ids)
    assert delegated_session_ids == []


@pytest.mark.parametrize(
    "review_payload",
    (
        pytest.param({"session_id": "session-001"}, id="missing-keys"),
        pytest.param(
            {
                "session_id": "session-001",
                "review_kind": "stored_session_window_recovery_review",
                "runtime_lifecycle_status": "not_started",
                "archive_recovery_status": "empty",
                "archive_existing_count": 0,
                "archive_missing_count": 6,
                "recovery_decision": "no_action",
                "manual_review_required": False,
                "review_status": "not_required",
                "review_reason": "none",
                "safe_next_review_action": "leave_archive_unchanged",
            },
            id="wrong-key-order",
        ),
        pytest.param(_review("session-002"), id="mismatched-session-id"),
        pytest.param(_review("../private"), id="unsafe-delegated-session-id"),
        pytest.param(_review("session-001", review_kind="other"), id="kind"),
        pytest.param(
            _review("session-001", runtime_lifecycle_status="unknown"),
            id="lifecycle",
        ),
        pytest.param(
            _review("session-001", archive_recovery_status="unknown"),
            id="archive-status",
        ),
        pytest.param(
            _review("session-001", archive_existing_count=True),
            id="bool-count",
        ),
        pytest.param(
            _review("session-001", recovery_decision="unknown"),
            id="recovery-decision",
        ),
        pytest.param(
            _review("session-001", manual_review_required="true"),
            id="manual-review-type",
        ),
        pytest.param(
            _review(
                "session-001",
                recovery_decision="inspect_active_session",
                manual_review_required=False,
                review_status="not_required",
                review_reason="none",
                safe_next_review_action="leave_archive_unchanged",
            ),
            id="manual-review-consistency",
        ),
        pytest.param(
            _review(
                "session-001",
                recovery_decision="manual_review",
                manual_review_required=True,
                review_status="required",
                review_reason="partial_archive_metadata",
                safe_next_review_action="inspect_archive_metadata",
            ),
            id="reason-action-consistency",
        ),
    ),
)
def test_build_recovery_review_batch_revalidates_delegated_payload(
    monkeypatch,
    review_payload: dict[str, object],
) -> None:
    monkeypatch.setattr(
        recovery_batch_review,
        "build_stored_session_window_recovery_review",
        lambda archive_root, session_id: review_payload,
    )

    _assert_batch_error(Path("archive-root"), ["session-001"])


@pytest.mark.parametrize(
    ("field_name", "expected_value"),
    (
        pytest.param("review_status", "not_required", id="review-status"),
        pytest.param("review_reason", "none", id="review-reason"),
        pytest.param(
            "safe_next_review_action",
            "leave_archive_unchanged",
            id="safe-next-review-action",
        ),
    ),
)
def test_build_recovery_review_batch_rejects_spoofed_delegated_string_scalars(
    monkeypatch,
    field_name: str,
    expected_value: str,
) -> None:
    review_payload = _review(
        "session-001",
        **{field_name: _SpoofedStringLike(expected_value)},
    )
    monkeypatch.setattr(
        recovery_batch_review,
        "build_stored_session_window_recovery_review",
        lambda archive_root, session_id: review_payload,
    )

    _assert_batch_error(Path("archive-root"), ["session-001"])


@pytest.mark.parametrize(
    ("field_name", "value", "equal_to"),
    (
        pytest.param(
            "review_kind",
            "private-review-kind",
            "stored_session_window_recovery_review",
            id="review-kind",
        ),
        pytest.param(
            "session_id",
            "private-session-id",
            "session-001",
            id="session-id",
        ),
        pytest.param(
            "runtime_lifecycle_status",
            "private-lifecycle-status",
            "not_started",
            id="lifecycle",
        ),
        pytest.param(
            "archive_recovery_status",
            "private-archive-status",
            "empty",
            id="archive-status",
        ),
        pytest.param(
            "recovery_decision",
            "private-recovery-decision",
            "no_action",
            id="recovery-decision",
        ),
        pytest.param(
            "review_status",
            "private-review-status",
            "not_required",
            id="review-status",
        ),
        pytest.param("review_reason", "private-review-reason", "none", id="reason"),
        pytest.param(
            "safe_next_review_action",
            "private-review-action",
            "leave_archive_unchanged",
            id="action",
        ),
    ),
)
def test_build_recovery_review_batch_rejects_spoofed_str_subclasses(
    monkeypatch,
    field_name: str,
    value: str,
    equal_to: str,
) -> None:
    review_payload = _review("session-001")
    review_payload[field_name] = _SpoofedStr(value, equal_to)
    monkeypatch.setattr(
        recovery_batch_review,
        "build_stored_session_window_recovery_review",
        lambda archive_root, session_id: review_payload,
    )

    _assert_batch_error(Path("archive-root"), ["session-001"])


def test_build_recovery_review_batch_sanitizes_delegated_failure(
    monkeypatch,
) -> None:
    def fake_build(archive_root: Path, session_id: str) -> dict[str, object]:
        raise ValueError("C:\\Users\\student\\token-secret-auth-profile")

    monkeypatch.setattr(
        recovery_batch_review,
        "build_stored_session_window_recovery_review",
        fake_build,
    )

    _assert_batch_error(Path("archive-root"), ["session-001"])


def test_build_recovery_review_batch_does_not_create_modify_or_delete_files(
    tmp_path: Path,
    monkeypatch,
) -> None:
    archive_root = tmp_path / "archive"
    archive_root.mkdir()
    existing_file = archive_root / "keep.txt"
    existing_file.write_text("existing", encoding="utf-8")

    monkeypatch.setattr(
        recovery_batch_review,
        "build_stored_session_window_recovery_review",
        lambda archive_root, session_id: _review(session_id),
    )

    build_stored_session_window_recovery_review_batch(
        archive_root,
        ["session-001", "session-002"],
    )

    assert existing_file.read_text(encoding="utf-8") == "existing"
    assert sorted(path.name for path in archive_root.iterdir()) == ["keep.txt"]


def test_build_recovery_review_batch_excludes_private_metadata(monkeypatch) -> None:
    monkeypatch.setattr(
        recovery_batch_review,
        "build_stored_session_window_recovery_review",
        lambda archive_root, session_id: _review(session_id),
    )

    batch = build_stored_session_window_recovery_review_batch(
        Path("C:\\Users\\student\\token-secret-auth-profile"),
        ["session-001"],
    )

    combined = repr(batch).lower()
    for forbidden_fragment in (
        "c:\\",
        "token",
        "secret",
        "auth",
        "profile",
        "transcript",
        "audio",
        "browser",
        "runtime.jsonl",
        "events.jsonl",
        "alerts.log",
        "reviewer.md",
        "gate d",
        "product promise",
    ):
        assert forbidden_fragment not in combined


def test_batch_review_source_guards_forbidden_execution_surfaces() -> None:
    source = inspect.getsource(recovery_batch_review).lower()

    assert "build_stored_session_window_recovery_review(" in source
    for forbidden_fragment in (
        "iterdir",
        "glob(",
        "rglob",
        "walk(",
        ".open(",
        ".read_text(",
        ".write_text(",
        ".mkdir(",
        ".unlink(",
        ".remove(",
        ".rmdir(",
        "rmtree",
        "runtime.jsonl",
        "build_stored_session_window_recovery_decision",
        "build_stored_session_window_runtime_summary",
        "build_crash_recovery_session_preflight",
        "archive_export",
        "archive_delete",
        "execute_archive",
        "scheduler",
        "sleep",
        "timer(",
        "threading",
        "asyncio",
        "subprocess",
        "webbrowser",
        "requests",
        "httpx",
        "playwright",
        "selenium",
        "sounddevice",
        "faster_whisper",
        "mic_recording",
        "telegram",
        "desktop_notifier",
        "alert_dispatch",
        "participation",
        "academic_answer",
        "gate d",
        "product promise",
    ):
        assert forbidden_fragment not in source
