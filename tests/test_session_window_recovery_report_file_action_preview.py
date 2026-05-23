from __future__ import annotations

import inspect

import pytest

from async_scholar import (
    session_window_recovery_report_file_action_preview as action_preview,
)
from async_scholar.session_window_recovery_report_file_action_preview import (
    STORED_SESSION_WINDOW_RECOVERY_REPORT_FILE_ACTION_PREVIEW_ERROR,
    build_stored_session_window_recovery_report_file_action_preview,
)

REPORT_PATH = "stored-session-window-recovery-report.md"
VERIFICATION_KIND = "stored_session_window_recovery_report_file_verification"
PREVIEW_KIND = "stored_session_window_recovery_report_file_action_preview"


def _verification_receipt(
    *,
    exists: bool = True,
    matches_expected: bool = True,
    session_count: int = 2,
    relative_path: str = REPORT_PATH,
    size_bytes: int = 123,
    expected_size_bytes: int = 123,
) -> dict[str, object]:
    return {
        "verification_kind": VERIFICATION_KIND,
        "session_count": session_count,
        "relative_path": relative_path,
        "exists": exists,
        "matches_expected": matches_expected,
        "size_bytes": size_bytes,
        "expected_size_bytes": expected_size_bytes,
    }


def _stub_verifier(monkeypatch, receipt: object) -> dict[str, object]:
    delegated: dict[str, object] = {}

    def fake_build(
        session_ids: object,
        archive_root: object,
        output_root: object,
    ) -> object:
        delegated["session_ids"] = session_ids
        delegated["archive_root"] = archive_root
        delegated["output_root"] = output_root
        return receipt

    monkeypatch.setattr(
        action_preview,
        "build_stored_session_window_recovery_report_file_verification",
        fake_build,
    )
    return delegated


def _assert_preview_error(
    session_ids: object,
    archive_root: object,
    output_root: object,
) -> None:
    with pytest.raises(ValueError) as exc_info:
        build_stored_session_window_recovery_report_file_action_preview(
            session_ids,  # type: ignore[arg-type]
            archive_root,
            output_root,
        )
    assert (
        str(exc_info.value)
        == STORED_SESSION_WINDOW_RECOVERY_REPORT_FILE_ACTION_PREVIEW_ERROR
    )


@pytest.mark.parametrize(
    ("verification_receipt", "recommended_action", "reason"),
    (
        pytest.param(
            _verification_receipt(
                exists=True,
                matches_expected=True,
                size_bytes=123,
                expected_size_bytes=123,
            ),
            "none",
            "report_already_current",
            id="current",
        ),
        pytest.param(
            _verification_receipt(
                exists=False,
                matches_expected=False,
                size_bytes=0,
                expected_size_bytes=123,
            ),
            "write_report",
            "report_missing",
            id="missing",
        ),
        pytest.param(
            _verification_receipt(
                exists=True,
                matches_expected=False,
                size_bytes=111,
                expected_size_bytes=123,
            ),
            "manual_review",
            "report_content_mismatch",
            id="mismatch",
        ),
    ),
)
def test_action_preview_maps_verification_state_to_safe_receipt(
    tmp_path,
    monkeypatch,
    verification_receipt: dict[str, object],
    recommended_action: str,
    reason: str,
) -> None:
    archive_root = tmp_path / "archive"
    output_root = tmp_path / "reports"
    delegated = _stub_verifier(monkeypatch, verification_receipt)

    receipt = build_stored_session_window_recovery_report_file_action_preview(
        ("session-001", "session-002"),
        archive_root,
        output_root,
    )

    assert tuple(receipt) == (
        "preview_kind",
        "session_count",
        "relative_path",
        "exists",
        "matches_expected",
        "recommended_action",
        "reason",
    )
    assert receipt == {
        "preview_kind": PREVIEW_KIND,
        "session_count": 2,
        "relative_path": REPORT_PATH,
        "exists": verification_receipt["exists"],
        "matches_expected": verification_receipt["matches_expected"],
        "recommended_action": recommended_action,
        "reason": reason,
    }
    assert delegated == {
        "session_ids": ("session-001", "session-002"),
        "archive_root": archive_root,
        "output_root": output_root,
    }


def test_action_preview_receipt_excludes_private_data(tmp_path, monkeypatch) -> None:
    _stub_verifier(
        monkeypatch,
        _verification_receipt(
            exists=True,
            matches_expected=False,
            size_bytes=987,
            expected_size_bytes=123,
        ),
    )

    receipt = build_stored_session_window_recovery_report_file_action_preview(
        ("session-001", "session-002"),
        tmp_path / "C-Users-student-token-secret-auth-profile",
        tmp_path / "reports",
    )

    combined_receipt = repr(receipt).lower()
    for forbidden_fragment in (
        str(tmp_path).lower(),
        "session-001",
        "session-002",
        "transcript",
        "source",
        "event",
        "runtime",
        "token",
        "secret",
        "auth",
        "profile",
        "url",
        "cookie",
        "recording",
        "generated media",
        "traceback",
        "overwrite",
        "delete",
        "export",
        "execute",
        "diff",
    ):
        assert forbidden_fragment not in combined_receipt


def test_action_preview_sanitizes_delegated_verifier_failure(
    tmp_path,
    monkeypatch,
) -> None:
    def fake_build(
        session_ids: object,
        archive_root: object,
        output_root: object,
    ) -> dict[str, object]:
        raise RuntimeError("C:\\Users\\student\\token-secret-auth-profile")

    monkeypatch.setattr(
        action_preview,
        "build_stored_session_window_recovery_report_file_verification",
        fake_build,
    )

    _assert_preview_error(
        ("session-001",),
        tmp_path / "archive",
        tmp_path / "reports",
    )


class _ReceiptSubclass(dict[str, object]):
    pass


@pytest.mark.parametrize(
    "malformed_receipt",
    (
        pytest.param(
            _ReceiptSubclass(_verification_receipt()),
            id="dict-subclass",
        ),
        pytest.param(
            [
                ("verification_kind", VERIFICATION_KIND),
                ("session_count", 2),
            ],
            id="not-dict",
        ),
        pytest.param(
            {
                **_verification_receipt(),
                "private_path": "C:\\Users\\student\\token-secret-auth-profile",
            },
            id="extra-private-field",
        ),
        pytest.param(
            {
                "session_count": 2,
                "verification_kind": VERIFICATION_KIND,
                "relative_path": REPORT_PATH,
                "exists": True,
                "matches_expected": True,
                "size_bytes": 123,
                "expected_size_bytes": 123,
            },
            id="wrong-key-order",
        ),
        pytest.param(
            {
                key: value
                for key, value in _verification_receipt().items()
                if key != "expected_size_bytes"
            },
            id="missing-key",
        ),
        pytest.param(
            {
                **_verification_receipt(),
                "verification_kind": "stored_session_window_recovery_report_file",
            },
            id="bad-verification-kind",
        ),
        pytest.param(
            {
                **_verification_receipt(),
                "relative_path": "C:\\Users\\student\\private-report.md",
            },
            id="absolute-private-relative-path",
        ),
        pytest.param(
            {
                **_verification_receipt(),
                "relative_path": "../stored-session-window-recovery-report.md",
            },
            id="traversal-relative-path",
        ),
        pytest.param(
            {
                **_verification_receipt(),
                "exists": "true",
            },
            id="string-bool",
        ),
        pytest.param(
            {
                **_verification_receipt(),
                "matches_expected": 1,
            },
            id="integer-bool",
        ),
        pytest.param(
            {
                **_verification_receipt(),
                "session_count": True,
            },
            id="bool-count",
        ),
        pytest.param(
            {
                **_verification_receipt(),
                "session_count": -1,
            },
            id="negative-count",
        ),
        pytest.param(
            {
                **_verification_receipt(),
                "size_bytes": True,
            },
            id="bool-size",
        ),
        pytest.param(
            {
                **_verification_receipt(),
                "expected_size_bytes": -1,
            },
            id="negative-expected-size",
        ),
        pytest.param(
            _verification_receipt(
                exists=False,
                matches_expected=True,
                size_bytes=0,
                expected_size_bytes=123,
            ),
            id="missing-but-matches",
        ),
        pytest.param(
            _verification_receipt(
                exists=False,
                matches_expected=False,
                size_bytes=1,
                expected_size_bytes=123,
            ),
            id="missing-with-size",
        ),
        pytest.param(
            _verification_receipt(
                exists=True,
                matches_expected=True,
                size_bytes=122,
                expected_size_bytes=123,
            ),
            id="matched-size-disagreement",
        ),
    ),
)
def test_action_preview_sanitizes_malformed_verifier_receipt(
    tmp_path,
    monkeypatch,
    malformed_receipt: object,
) -> None:
    _stub_verifier(monkeypatch, malformed_receipt)

    _assert_preview_error(
        ("session-001", "session-002"),
        tmp_path / "archive",
        tmp_path / "reports",
    )


def test_action_preview_does_not_create_modify_or_delete_files(
    tmp_path,
    monkeypatch,
) -> None:
    archive_root = tmp_path / "archive"
    output_root = tmp_path / "reports"
    archive_root.mkdir()
    output_root.mkdir()
    archive_marker = archive_root / "keep.txt"
    output_marker = output_root / "keep.txt"
    report_path = output_root / REPORT_PATH
    archive_marker.write_text("archive", encoding="utf-8")
    output_marker.write_text("output", encoding="utf-8")
    report_path.write_text("private existing report", encoding="utf-8")
    _stub_verifier(
        monkeypatch,
        _verification_receipt(
            exists=True,
            matches_expected=False,
            size_bytes=23,
            expected_size_bytes=123,
        ),
    )

    build_stored_session_window_recovery_report_file_action_preview(
        ("session-001", "session-002"),
        archive_root,
        output_root,
    )

    assert archive_marker.read_text(encoding="utf-8") == "archive"
    assert output_marker.read_text(encoding="utf-8") == "output"
    assert report_path.read_text(encoding="utf-8") == "private existing report"
    assert sorted(path.name for path in archive_root.iterdir()) == ["keep.txt"]
    assert sorted(path.name for path in output_root.iterdir()) == [
        "keep.txt",
        REPORT_PATH,
    ]


def test_action_preview_source_stays_read_only_and_narrow() -> None:
    source = inspect.getsource(action_preview)

    assert "build_stored_session_window_recovery_report_file_verification" in source
    assert "stored-session-window-recovery-report.md" in source
    for forbidden_fragment in (
        "build_stored_session_window_recovery_report_file_inventory",
        "write_stored_session_window_recovery_report_file",
        "build_stored_session_window_recovery_report(",
        "build_stored_session_window_recovery_review_batch",
        "build_stored_session_window_recovery_review(",
        "build_stored_session_window_recovery_decision",
        "build_stored_session_window_runtime_summary",
        "build_crash_recovery_session_preflight",
        "list_course_schedule_session_window_inputs",
        "load_course_schedule",
        "save_course_schedule",
        "initialize_course_schedule_store",
        "ScheduleConfig",
        "CourseMetadata",
        "ScheduledStartClock",
        "execute_archive",
        "archive_export",
        "archive_delete",
        ".write_text(",
        ".write_bytes(",
        ".mkdir(",
        ".unlink(",
        ".remove(",
        ".rmdir(",
        "rmtree",
        "iterdir(",
        "glob(",
        "walk(",
        "open(",
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
