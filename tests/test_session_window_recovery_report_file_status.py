from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from async_scholar import (
    session_window_recovery_report_file_status as recovery_report_status,
)
from async_scholar.session_window_recovery_report_file_status import (
    STORED_SESSION_WINDOW_RECOVERY_REPORT_FILE_STATUS_ERROR,
    build_stored_session_window_recovery_report_file_status,
)

REPORT_PATH = "stored-session-window-recovery-report.md"
STATUS_KEYS = (
    "status_kind",
    "session_count",
    "relative_path",
    "exists",
    "matches_expected",
    "size_bytes",
    "expected_size_bytes",
    "recommended_action",
    "reason",
)
VERIFICATION_KEYS = (
    "verification_kind",
    "session_count",
    "relative_path",
    "exists",
    "matches_expected",
    "size_bytes",
    "expected_size_bytes",
)


class _DictSubclass(dict):
    pass


class _SpoofedString(str):
    def __eq__(self, other: object) -> bool:
        return True


def _verification_receipt(
    *,
    exists: bool = True,
    matches_expected: bool = True,
    size_bytes: int = 128,
    expected_size_bytes: int = 128,
    session_count: int = 2,
    relative_path: object = REPORT_PATH,
    verification_kind: object = (
        "stored_session_window_recovery_report_file_verification"
    ),
) -> dict[str, object]:
    return {
        "verification_kind": verification_kind,
        "session_count": session_count,
        "relative_path": relative_path,
        "exists": exists,
        "matches_expected": matches_expected,
        "size_bytes": size_bytes,
        "expected_size_bytes": expected_size_bytes,
    }


def _stub_verification(monkeypatch, receipt: object) -> dict[str, object]:
    delegated: dict[str, object] = {}

    def fake_build(
        session_ids: tuple[str, ...],
        archive_root: Path,
        output_root: Path,
    ) -> object:
        delegated["session_ids"] = session_ids
        delegated["archive_root"] = archive_root
        delegated["output_root"] = output_root
        return receipt

    monkeypatch.setattr(
        recovery_report_status,
        "build_stored_session_window_recovery_report_file_verification",
        fake_build,
    )
    return delegated


def _assert_status_error(
    session_ids: tuple[str, ...],
    archive_root: Path,
    output_root: Path,
) -> None:
    with pytest.raises(ValueError) as exc_info:
        build_stored_session_window_recovery_report_file_status(
            session_ids,
            archive_root,
            output_root,
        )
    assert (
        str(exc_info.value) == STORED_SESSION_WINDOW_RECOVERY_REPORT_FILE_STATUS_ERROR
    )


@pytest.mark.parametrize(
    (
        "verification",
        "recommended_action",
        "reason",
    ),
    (
        pytest.param(
            _verification_receipt(
                exists=True,
                matches_expected=True,
                size_bytes=128,
                expected_size_bytes=128,
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
                expected_size_bytes=128,
            ),
            "write_report",
            "report_missing",
            id="missing",
        ),
        pytest.param(
            _verification_receipt(
                exists=True,
                matches_expected=False,
                size_bytes=14,
                expected_size_bytes=128,
            ),
            "manual_review",
            "report_content_mismatch",
            id="mismatched",
        ),
    ),
)
def test_status_maps_verified_file_states_to_safe_receipts(
    tmp_path,
    monkeypatch,
    verification: dict[str, object],
    recommended_action: str,
    reason: str,
) -> None:
    archive_root = tmp_path / "archive"
    output_root = tmp_path / "reports"
    archive_root.mkdir()
    output_root.mkdir()
    delegated = _stub_verification(monkeypatch, verification)

    receipt = build_stored_session_window_recovery_report_file_status(
        ("session-001", "session-002"),
        archive_root,
        output_root,
    )

    assert type(receipt) is dict
    assert tuple(receipt) == STATUS_KEYS
    assert receipt == {
        "status_kind": "stored_session_window_recovery_report_file_status",
        "session_count": 2,
        "relative_path": REPORT_PATH,
        "exists": verification["exists"],
        "matches_expected": verification["matches_expected"],
        "size_bytes": verification["size_bytes"],
        "expected_size_bytes": verification["expected_size_bytes"],
        "recommended_action": recommended_action,
        "reason": reason,
    }
    assert delegated == {
        "session_ids": ("session-001", "session-002"),
        "archive_root": archive_root,
        "output_root": output_root,
    }
    assert not (output_root / REPORT_PATH).exists()


@pytest.mark.parametrize(
    "receipt",
    (
        pytest.param(
            _DictSubclass(_verification_receipt()),
            id="dict-subclass",
        ),
        pytest.param(
            {
                "session_count": 2,
                "verification_kind": (
                    "stored_session_window_recovery_report_file_verification"
                ),
                "relative_path": REPORT_PATH,
                "exists": True,
                "matches_expected": True,
                "size_bytes": 128,
                "expected_size_bytes": 128,
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
            {**_verification_receipt(), "private_path": "C:\\Users\\student\\secret"},
            id="extra-key",
        ),
        pytest.param(
            _verification_receipt(verification_kind="wrong"),
            id="bad-kind",
        ),
        pytest.param(
            _verification_receipt(
                verification_kind=_SpoofedString(
                    "stored_session_window_recovery_report_file_verification"
                )
            ),
            id="spoofed-kind",
        ),
        pytest.param(
            _verification_receipt(relative_path="C:\\Users\\student\\secret.md"),
            id="absolute-private-path",
        ),
        pytest.param(
            _verification_receipt(relative_path="../stored-session-window.md"),
            id="traversal-path",
        ),
        pytest.param(
            _verification_receipt(
                relative_path="reports/stored-session-window-recovery-report.md"
            ),
            id="extra-path-separator",
        ),
        pytest.param(
            _verification_receipt(relative_path=_SpoofedString(REPORT_PATH)),
            id="spoofed-path",
        ),
        pytest.param(
            _verification_receipt(session_count=True),
            id="bool-session-count",
        ),
        pytest.param(
            _verification_receipt(session_count=0),
            id="zero-session-count",
        ),
        pytest.param(
            _verification_receipt(exists=1),
            id="non-bool-exists",
        ),
        pytest.param(
            _verification_receipt(matches_expected=0),
            id="non-bool-matches",
        ),
        pytest.param(
            _verification_receipt(size_bytes=True),
            id="bool-size",
        ),
        pytest.param(
            _verification_receipt(expected_size_bytes=False),
            id="bool-expected-size",
        ),
        pytest.param(
            _verification_receipt(size_bytes=-1),
            id="negative-size",
        ),
        pytest.param(
            _verification_receipt(expected_size_bytes=-1),
            id="negative-expected-size",
        ),
        pytest.param(
            _verification_receipt(
                exists=False,
                matches_expected=True,
                size_bytes=0,
                expected_size_bytes=128,
            ),
            id="missing-but-matches",
        ),
        pytest.param(
            _verification_receipt(
                exists=False,
                matches_expected=False,
                size_bytes=1,
                expected_size_bytes=128,
            ),
            id="missing-with-size",
        ),
        pytest.param(
            _verification_receipt(
                exists=True,
                matches_expected=True,
                size_bytes=127,
                expected_size_bytes=128,
            ),
            id="matched-size-disagreement",
        ),
        pytest.param(
            _verification_receipt(
                exists=True,
                matches_expected=True,
                size_bytes=0,
                expected_size_bytes=0,
            ),
            id="present-current-invalid-size",
        ),
        pytest.param(
            _verification_receipt(
                exists=True,
                matches_expected=False,
                size_bytes=1,
                expected_size_bytes=0,
            ),
            id="invalid-expected-size",
        ),
    ),
)
def test_status_rejects_malformed_delegated_receipts(
    tmp_path,
    monkeypatch,
    receipt: object,
) -> None:
    archive_root = tmp_path / "archive"
    output_root = tmp_path / "reports"
    archive_root.mkdir()
    output_root.mkdir()
    _stub_verification(monkeypatch, receipt)

    _assert_status_error(("session-001", "session-002"), archive_root, output_root)


def test_status_sanitizes_delegated_failures(tmp_path, monkeypatch) -> None:
    archive_root = tmp_path / "archive"
    output_root = tmp_path / "reports"
    archive_root.mkdir()
    output_root.mkdir()

    def fake_build(
        session_ids: tuple[str, ...],
        archive_root_arg: Path,
        output_root_arg: Path,
    ) -> object:
        raise RuntimeError(
            "C:\\Users\\student\\token-secret-auth-profile transcript text"
        )

    monkeypatch.setattr(
        recovery_report_status,
        "build_stored_session_window_recovery_report_file_verification",
        fake_build,
    )

    _assert_status_error(("session-001",), archive_root, output_root)


def test_status_success_receipts_exclude_private_data(tmp_path, monkeypatch) -> None:
    archive_root = tmp_path / "archive"
    output_root = tmp_path / "reports"
    archive_root.mkdir()
    output_root.mkdir()
    _stub_verification(monkeypatch, _verification_receipt())

    receipt = build_stored_session_window_recovery_report_file_status(
        ("private-session-001", "private-session-002"),
        archive_root,
        output_root,
    )

    rendered = repr(receipt)
    for forbidden_fragment in (
        str(tmp_path),
        "private-session-001",
        "private-session-002",
        "transcript",
        "source",
        "runtime",
        "diff",
        "https://",
        "token",
        "auth",
        "recording",
        "generated media",
        "secret",
        "Traceback",
    ):
        assert forbidden_fragment not in rendered


def test_status_module_delegates_only_to_verification() -> None:
    source = inspect.getsource(recovery_report_status)

    assert "build_stored_session_window_recovery_report_file_verification" in source
    for forbidden_fragment in (
        "build_stored_session_window_recovery_report_file_action_preview",
        "build_stored_session_window_recovery_report_file_action",
        "write_stored_session_window_recovery_report_file",
        "build_stored_session_window_recovery_report_file_inventory",
        "build_stored_session_window_recovery_report(",
        "build_stored_session_window_recovery_review_batch",
        "build_stored_session_window_recovery_review(",
        "build_stored_session_window_recovery_decision",
        "archive_export",
        "archive_delete",
        "subprocess",
        "Popen",
        "run(",
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
        "open(",
        "unlink",
        "rmdir",
        "remove(",
        "replace(",
        "rename(",
    ):
        assert forbidden_fragment not in source
