from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from async_scholar import (
    session_window_recovery_report as recovery_report,
)
from async_scholar.session_window_recovery_report import (
    STORED_SESSION_WINDOW_RECOVERY_REPORT_ERROR,
    build_stored_session_window_recovery_report,
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


def _batch(*reviews: dict[str, object], **overrides: object) -> dict[str, object]:
    required_count = sum(
        1 for review in reviews if review["review_status"] == "required"
    )
    payload: dict[str, object] = {
        "batch_kind": "stored_session_window_recovery_review_batch",
        "review_count": len(reviews),
        "manual_review_required_count": sum(
            1 for review in reviews if review["manual_review_required"] is True
        ),
        "not_required_count": len(reviews) - required_count,
        "required_count": required_count,
        "reviews": list(reviews),
    }
    payload.update(overrides)
    return payload


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


class _DelegatedBatchDict(dict):
    pass


def _assert_report_error(archive_root: object, session_ids: object) -> None:
    with pytest.raises(ValueError) as exc_info:
        build_stored_session_window_recovery_report(
            archive_root,  # type: ignore[arg-type]
            session_ids,  # type: ignore[arg-type]
        )
    assert str(exc_info.value) == STORED_SESSION_WINDOW_RECOVERY_REPORT_ERROR


def test_build_recovery_report_renders_deterministic_markdown(monkeypatch) -> None:
    delegated: dict[str, object] = {}

    def fake_build(
        archive_root: Path, session_ids: tuple[str, ...]
    ) -> dict[str, object]:
        delegated["archive_root"] = archive_root
        delegated["session_ids"] = session_ids
        return _batch(
            _review(
                "session-002",
                recovery_decision="manual_review",
                manual_review_required=True,
                review_status="required",
                review_reason="inconsistent_runtime",
                safe_next_review_action="escalate_manual_review",
                runtime_lifecycle_status="inconsistent",
                archive_recovery_status="partial",
                archive_existing_count=1,
            ),
            _review("session-001"),
        )

    monkeypatch.setattr(
        recovery_report,
        "build_stored_session_window_recovery_review_batch",
        fake_build,
    )

    report = build_stored_session_window_recovery_report(
        Path("archive-root"),
        ("session-002", "session-001"),
    )

    assert report == (
        "# Stored Session Window Recovery Report\n"
        "\n"
        "Review count: 2\n"
        "Manual review required: 1\n"
        "Required: 1\n"
        "Not required: 1\n"
        "\n"
        "## session-002\n"
        "- Session ID: session-002\n"
        "- Lifecycle status: inconsistent\n"
        "- Archive status: partial\n"
        "- Recovery decision: manual_review\n"
        "- Review status: required\n"
        "- Review reason: inconsistent_runtime\n"
        "- Safe next review action: escalate_manual_review\n"
        "\n"
        "## session-001\n"
        "- Session ID: session-001\n"
        "- Lifecycle status: not_started\n"
        "- Archive status: empty\n"
        "- Recovery decision: no_action\n"
        "- Review status: not_required\n"
        "- Review reason: none\n"
        "- Safe next review action: leave_archive_unchanged\n"
    )
    assert (
        build_stored_session_window_recovery_report(
            Path("archive-root"),
            ("session-002", "session-001"),
        )
        == report
    )
    assert delegated == {
        "archive_root": Path("archive-root"),
        "session_ids": ("session-002", "session-001"),
    }


@pytest.mark.parametrize(
    "batch_payload",
    (
        pytest.param({"reviews": []}, id="missing-keys"),
        pytest.param(
            {
                "reviews": [],
                "batch_kind": "stored_session_window_recovery_review_batch",
                "review_count": 0,
                "manual_review_required_count": 0,
                "not_required_count": 0,
                "required_count": 0,
            },
            id="wrong-key-order",
        ),
        pytest.param(_batch(_review("session-001"), batch_kind="other"), id="kind"),
        pytest.param(
            _batch(_review("session-001"), review_count=True), id="bool-count"
        ),
        pytest.param(
            _batch(_review("session-001"), review_count=2), id="bad-review-count"
        ),
        pytest.param(
            _batch(_review("session-001"), required_count=1), id="bad-required-count"
        ),
        pytest.param(
            _batch(_review("session-001"), not_required_count=0),
            id="bad-not-required-count",
        ),
        pytest.param(
            _batch(_review("session-001"), manual_review_required_count=1),
            id="bad-manual-review-count",
        ),
        pytest.param(
            _batch(_review("session-001"), reviews=("not-a-list",)),
            id="bad-review-list-shape",
        ),
        pytest.param(
            _DelegatedBatchDict(_batch(_review("session-001"))),
            id="dict-subclass",
        ),
        pytest.param(_batch(_review("session-002")), id="mismatched-session-id"),
        pytest.param(_batch(_review("../private")), id="unsafe-session-id"),
        pytest.param(
            _batch(_review("session-001", review_kind="other")), id="review-kind"
        ),
        pytest.param(
            _batch(_review("session-001", runtime_lifecycle_status="unknown")),
            id="lifecycle",
        ),
        pytest.param(
            _batch(_review("session-001", archive_recovery_status="unknown")),
            id="archive-status",
        ),
        pytest.param(
            _batch(_review("session-001", archive_existing_count=1)),
            id="archive-count-not-rendered-but-revalidated",
        ),
        pytest.param(
            _batch(_review("session-001", recovery_decision="unknown")), id="decision"
        ),
        pytest.param(
            _batch(_review("session-001", manual_review_required="true")),
            id="manual-type",
        ),
        pytest.param(
            _batch(
                _review(
                    "session-001",
                    recovery_decision="inspect_active_session",
                    manual_review_required=False,
                    review_status="not_required",
                )
            ),
            id="consistency",
        ),
    ),
)
def test_build_recovery_report_revalidates_delegated_payload(
    monkeypatch,
    batch_payload: dict[str, object],
) -> None:
    monkeypatch.setattr(
        recovery_report,
        "build_stored_session_window_recovery_review_batch",
        lambda archive_root, session_ids: batch_payload,
    )

    _assert_report_error(Path("archive-root"), ["session-001"])


def test_build_recovery_report_rejects_spoofed_str_subclasses(monkeypatch) -> None:
    payload = _batch(_review("session-001"))
    reviews = payload["reviews"]
    assert isinstance(reviews, list)
    reviews[0]["review_status"] = _SpoofedStr("private-review-status", "not_required")
    monkeypatch.setattr(
        recovery_report,
        "build_stored_session_window_recovery_review_batch",
        lambda archive_root, session_ids: payload,
    )

    _assert_report_error(Path("archive-root"), ["session-001"])


def test_build_recovery_report_sanitizes_delegated_failure(monkeypatch) -> None:
    def fake_build(
        archive_root: Path, session_ids: tuple[str, ...]
    ) -> dict[str, object]:
        raise ValueError("C:\\Users\\student\\token-secret-auth-profile")

    monkeypatch.setattr(
        recovery_report,
        "build_stored_session_window_recovery_review_batch",
        fake_build,
    )

    _assert_report_error(Path("archive-root"), ["session-001"])


def test_build_recovery_report_does_not_create_modify_or_delete_files(
    tmp_path: Path,
    monkeypatch,
) -> None:
    archive_root = tmp_path / "archive"
    archive_root.mkdir()
    existing_file = archive_root / "keep.txt"
    existing_file.write_text("existing", encoding="utf-8")
    monkeypatch.setattr(
        recovery_report,
        "build_stored_session_window_recovery_review_batch",
        lambda archive_root, session_ids: _batch(
            *(_review(session_id) for session_id in session_ids)
        ),
    )

    build_stored_session_window_recovery_report(
        archive_root,
        ["session-001", "session-002"],
    )

    assert existing_file.read_text(encoding="utf-8") == "existing"
    assert sorted(path.name for path in archive_root.iterdir()) == ["keep.txt"]


def test_build_recovery_report_excludes_private_and_non_allowlisted_metadata(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        recovery_report,
        "build_stored_session_window_recovery_review_batch",
        lambda archive_root, session_ids: _batch(_review("session-001")),
    )

    report = build_stored_session_window_recovery_report(
        Path("C:\\Users\\student\\token-secret-auth-profile"),
        ["session-001"],
    ).lower()

    for forbidden_fragment in (
        "archive existing",
        "archive missing",
        "archive_existing_count",
        "archive_missing_count",
        "c:\\",
        "token",
        "secret",
        "auth",
        "profile",
        "transcript",
        "source",
        "event",
        "runtime.jsonl",
        "url",
        "browser",
        "recording",
        "media",
        "traceback",
        "gate d",
        "product promise",
    ):
        assert forbidden_fragment not in report


def test_recovery_report_source_guards_forbidden_execution_surfaces() -> None:
    source = inspect.getsource(recovery_report).lower()

    assert "build_stored_session_window_recovery_review_batch(" in source
    for forbidden_fragment in (
        "build_stored_session_window_recovery_review(",
        "build_stored_session_window_recovery_decision",
        "build_stored_session_window_runtime_summary",
        "build_crash_recovery_session_preflight",
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
