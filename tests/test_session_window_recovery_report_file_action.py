from __future__ import annotations

import inspect
import sys
import types

import pytest

from async_scholar import session_window_recovery_report_file_action as action
from async_scholar.session_window_recovery_report_file_action import (
    STORED_SESSION_WINDOW_RECOVERY_REPORT_FILE_ACTION_ERROR,
    build_stored_session_window_recovery_report_file_action,
)

REPORT_PATH = "stored-session-window-recovery-report.md"
PREVIEW_KIND = "stored_session_window_recovery_report_file_action_preview"
ACTION_KIND = "stored_session_window_recovery_report_file_action"
WRITE_KIND = "stored_session_window_recovery_report_file"


def _preview_receipt(
    *,
    session_count: int = 2,
    exists: bool = False,
    matches_expected: bool = False,
    recommended_action: str = "write_report",
    reason: str = "report_missing",
    relative_path: str = REPORT_PATH,
) -> dict[str, object]:
    return {
        "preview_kind": PREVIEW_KIND,
        "session_count": session_count,
        "relative_path": relative_path,
        "exists": exists,
        "matches_expected": matches_expected,
        "recommended_action": recommended_action,
        "reason": reason,
    }


def _writer_receipt(
    *,
    session_count: int = 2,
    relative_path: str = REPORT_PATH,
    bytes_written: int = 123,
) -> dict[str, object]:
    return {
        "write_kind": WRITE_KIND,
        "session_count": session_count,
        "relative_path": relative_path,
        "bytes_written": bytes_written,
    }


def _stub_preview(
    monkeypatch: pytest.MonkeyPatch, receipt: object
) -> dict[str, object]:
    delegated: dict[str, object] = {}

    def fake_preview(
        session_ids: object,
        archive_root: object,
        output_root: object,
    ) -> object:
        delegated["session_ids"] = session_ids
        delegated["archive_root"] = archive_root
        delegated["output_root"] = output_root
        return receipt

    monkeypatch.setattr(
        action,
        "build_stored_session_window_recovery_report_file_action_preview",
        fake_preview,
    )
    return delegated


def _stub_writer_module(
    monkeypatch: pytest.MonkeyPatch,
    receipt: object,
) -> dict[str, object]:
    delegated: dict[str, object] = {}
    writer_module_name = "async_scholar.session_window_recovery_report_file"
    fake_writer_module = types.ModuleType(writer_module_name)

    def fake_write(
        archive_root: object,
        output_root: object,
        session_ids: object,
    ) -> object:
        delegated["archive_root"] = archive_root
        delegated["output_root"] = output_root
        delegated["session_ids"] = session_ids
        return receipt

    fake_writer_module.__dict__["write_stored_session_window_recovery_report_file"] = (
        fake_write
    )
    monkeypatch.setitem(sys.modules, writer_module_name, fake_writer_module)
    return delegated


def _assert_action_error(
    session_ids: object,
    archive_root: object,
    output_root: object,
) -> None:
    with pytest.raises(ValueError) as exc_info:
        build_stored_session_window_recovery_report_file_action(
            session_ids,  # type: ignore[arg-type]
            archive_root,
            output_root,
        )
    assert (
        str(exc_info.value) == STORED_SESSION_WINDOW_RECOVERY_REPORT_FILE_ACTION_ERROR
    )


def test_action_writes_missing_report_after_valid_preview_and_writer_receipts(
    tmp_path,
    monkeypatch,
) -> None:
    archive_root = tmp_path / "archive"
    output_root = tmp_path / "reports"
    preview_delegated = _stub_preview(monkeypatch, _preview_receipt())
    writer_delegated = _stub_writer_module(monkeypatch, _writer_receipt())

    receipt = build_stored_session_window_recovery_report_file_action(
        ("session-001", "session-002"),
        archive_root,
        output_root,
    )

    assert tuple(receipt) == (
        "action_kind",
        "session_count",
        "relative_path",
        "preview_action",
        "preview_reason",
        "outcome",
        "bytes_written",
    )
    assert receipt == {
        "action_kind": ACTION_KIND,
        "session_count": 2,
        "relative_path": REPORT_PATH,
        "preview_action": "write_report",
        "preview_reason": "report_missing",
        "outcome": "written",
        "bytes_written": 123,
    }
    assert preview_delegated == {
        "session_ids": ("session-001", "session-002"),
        "archive_root": archive_root,
        "output_root": output_root,
    }
    assert writer_delegated == {
        "session_ids": ("session-001", "session-002"),
        "archive_root": archive_root,
        "output_root": output_root,
    }


@pytest.mark.parametrize(
    ("preview", "outcome"),
    (
        pytest.param(
            _preview_receipt(
                exists=True,
                matches_expected=True,
                recommended_action="none",
                reason="report_already_current",
            ),
            "no_action",
            id="current",
        ),
        pytest.param(
            _preview_receipt(
                exists=True,
                matches_expected=False,
                recommended_action="manual_review",
                reason="report_content_mismatch",
            ),
            "manual_review_required",
            id="mismatch",
        ),
    ),
)
def test_action_no_ops_without_importing_writer_for_current_or_mismatch_reports(
    tmp_path,
    monkeypatch,
    preview: dict[str, object],
    outcome: str,
) -> None:
    writer_module_name = "async_scholar.session_window_recovery_report_file"
    monkeypatch.delitem(sys.modules, writer_module_name, raising=False)
    _stub_preview(monkeypatch, preview)

    receipt = build_stored_session_window_recovery_report_file_action(
        ("session-001", "session-002"),
        tmp_path / "archive",
        tmp_path / "reports",
    )

    assert receipt == {
        "action_kind": ACTION_KIND,
        "session_count": 2,
        "relative_path": REPORT_PATH,
        "preview_action": preview["recommended_action"],
        "preview_reason": preview["reason"],
        "outcome": outcome,
        "bytes_written": 0,
    }
    assert writer_module_name not in sys.modules


def test_action_receipts_exclude_private_data(tmp_path, monkeypatch) -> None:
    _stub_preview(monkeypatch, _preview_receipt())
    _stub_writer_module(monkeypatch, _writer_receipt(bytes_written=321))

    receipt = build_stored_session_window_recovery_report_file_action(
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


def test_action_sanitizes_delegated_preview_failure(tmp_path, monkeypatch) -> None:
    def fake_preview(
        session_ids: object,
        archive_root: object,
        output_root: object,
    ) -> dict[str, object]:
        raise RuntimeError("C:\\Users\\student\\token-secret-auth-profile")

    monkeypatch.setattr(
        action,
        "build_stored_session_window_recovery_report_file_action_preview",
        fake_preview,
    )

    _assert_action_error(("session-001",), tmp_path / "archive", tmp_path / "reports")


def test_action_sanitizes_delegated_writer_failure(tmp_path, monkeypatch) -> None:
    _stub_preview(monkeypatch, _preview_receipt())
    writer_module_name = "async_scholar.session_window_recovery_report_file"
    fake_writer_module = types.ModuleType(writer_module_name)

    def fake_write(
        archive_root: object,
        output_root: object,
        session_ids: object,
    ) -> dict[str, object]:
        raise OSError("C:\\Users\\student\\token-secret-auth-profile")

    fake_writer_module.__dict__["write_stored_session_window_recovery_report_file"] = (
        fake_write
    )
    monkeypatch.setitem(sys.modules, writer_module_name, fake_writer_module)

    _assert_action_error(("session-001",), tmp_path / "archive", tmp_path / "reports")


class _ReceiptSubclass(dict[str, object]):
    pass


class _EqualitySpoof:
    def __init__(self, value: str) -> None:
        self.value = value

    def __eq__(self, other: object) -> bool:
        return other == self.value


@pytest.mark.parametrize(
    "malformed_preview",
    (
        pytest.param(_ReceiptSubclass(_preview_receipt()), id="dict-subclass"),
        pytest.param([("preview_kind", PREVIEW_KIND)], id="not-dict"),
        pytest.param(
            {
                **_preview_receipt(),
                "private_path": "C:\\Users\\student\\token-secret-auth-profile",
            },
            id="extra-private-field",
        ),
        pytest.param(
            {
                "session_count": 2,
                "preview_kind": PREVIEW_KIND,
                "relative_path": REPORT_PATH,
                "exists": False,
                "matches_expected": False,
                "recommended_action": "write_report",
                "reason": "report_missing",
            },
            id="wrong-key-order",
        ),
        pytest.param(
            {
                key: value
                for key, value in _preview_receipt().items()
                if key != "reason"
            },
            id="missing-key",
        ),
        pytest.param(
            {
                **_preview_receipt(),
                "preview_kind": "stored_session_window_recovery_report_file",
            },
            id="bad-preview-kind",
        ),
        pytest.param(
            {
                **_preview_receipt(),
                "preview_kind": _EqualitySpoof(PREVIEW_KIND),
            },
            id="spoof-preview-kind",
        ),
        pytest.param(
            {
                **_preview_receipt(),
                "relative_path": "C:\\Users\\student\\private-report.md",
            },
            id="absolute-private-path",
        ),
        pytest.param(
            {
                **_preview_receipt(),
                "relative_path": _EqualitySpoof(REPORT_PATH),
            },
            id="spoof-relative-path",
        ),
        pytest.param(
            {
                **_preview_receipt(),
                "recommended_action": _EqualitySpoof("write_report"),
            },
            id="spoof-recommended-action",
        ),
        pytest.param(
            {
                **_preview_receipt(),
                "reason": _EqualitySpoof("report_missing"),
            },
            id="spoof-reason",
        ),
        pytest.param(
            {
                **_preview_receipt(),
                "session_count": True,
            },
            id="bool-session-count",
        ),
        pytest.param(
            {
                **_preview_receipt(),
                "session_count": 0,
            },
            id="zero-session-count",
        ),
        pytest.param(
            {
                **_preview_receipt(),
                "exists": "false",
            },
            id="string-exists",
        ),
        pytest.param(
            {
                **_preview_receipt(),
                "matches_expected": 0,
            },
            id="integer-matches",
        ),
        pytest.param(
            _preview_receipt(
                exists=True,
                matches_expected=True,
                recommended_action="write_report",
                reason="report_already_current",
            ),
            id="current-write-action",
        ),
        pytest.param(
            _preview_receipt(
                exists=False,
                matches_expected=False,
                recommended_action="manual_review",
                reason="report_missing",
            ),
            id="missing-manual-review-action",
        ),
        pytest.param(
            _preview_receipt(
                exists=True,
                matches_expected=False,
                recommended_action="none",
                reason="report_content_mismatch",
            ),
            id="mismatch-none-action",
        ),
    ),
)
def test_action_sanitizes_malformed_preview_receipts(
    tmp_path,
    monkeypatch,
    malformed_preview: object,
) -> None:
    _stub_preview(monkeypatch, malformed_preview)
    _stub_writer_module(monkeypatch, _writer_receipt())

    _assert_action_error(
        ("session-001", "session-002"),
        tmp_path / "archive",
        tmp_path / "reports",
    )


@pytest.mark.parametrize(
    "malformed_writer",
    (
        pytest.param(_ReceiptSubclass(_writer_receipt()), id="dict-subclass"),
        pytest.param([("write_kind", WRITE_KIND)], id="not-dict"),
        pytest.param(
            {
                **_writer_receipt(),
                "private_path": "C:\\Users\\student\\token-secret-auth-profile",
            },
            id="extra-private-field",
        ),
        pytest.param(
            {
                "session_count": 2,
                "write_kind": WRITE_KIND,
                "relative_path": REPORT_PATH,
                "bytes_written": 123,
            },
            id="wrong-key-order",
        ),
        pytest.param(
            {
                key: value
                for key, value in _writer_receipt().items()
                if key != "bytes_written"
            },
            id="missing-key",
        ),
        pytest.param(
            {
                **_writer_receipt(),
                "write_kind": "stored_session_window_recovery_report_file_action",
            },
            id="bad-write-kind",
        ),
        pytest.param(
            {
                **_writer_receipt(),
                "write_kind": _EqualitySpoof(WRITE_KIND),
            },
            id="spoof-write-kind",
        ),
        pytest.param(
            {
                **_writer_receipt(),
                "relative_path": "../stored-session-window-recovery-report.md",
            },
            id="bad-relative-path",
        ),
        pytest.param(
            {
                **_writer_receipt(),
                "relative_path": _EqualitySpoof(REPORT_PATH),
            },
            id="spoof-relative-path",
        ),
        pytest.param(
            {
                **_writer_receipt(),
                "session_count": 1,
            },
            id="count-mismatch",
        ),
        pytest.param(
            {
                **_writer_receipt(),
                "session_count": True,
            },
            id="bool-session-count",
        ),
        pytest.param(
            {
                **_writer_receipt(),
                "bytes_written": True,
            },
            id="bool-bytes",
        ),
        pytest.param(
            {
                **_writer_receipt(),
                "bytes_written": 0,
            },
            id="zero-bytes",
        ),
        pytest.param(
            {
                **_writer_receipt(),
                "bytes_written": -1,
            },
            id="negative-bytes",
        ),
    ),
)
def test_action_sanitizes_malformed_writer_receipts(
    tmp_path,
    monkeypatch,
    malformed_writer: object,
) -> None:
    _stub_preview(monkeypatch, _preview_receipt())
    _stub_writer_module(monkeypatch, malformed_writer)

    _assert_action_error(
        ("session-001", "session-002"),
        tmp_path / "archive",
        tmp_path / "reports",
    )


def test_action_sanitizes_race_where_report_appears_before_writer(
    tmp_path,
    monkeypatch,
) -> None:
    archive_root = tmp_path / "archive"
    output_root = tmp_path / "reports"
    archive_root.mkdir()
    output_root.mkdir()
    destination = output_root / REPORT_PATH

    def fake_preview(
        session_ids: object,
        archive_root_arg: object,
        output_root_arg: object,
    ) -> dict[str, object]:
        assert session_ids == ("session-001",)
        assert archive_root_arg == archive_root
        assert output_root_arg == output_root
        destination.write_text("late private report", encoding="utf-8")
        return _preview_receipt(session_count=1)

    monkeypatch.setattr(
        action,
        "build_stored_session_window_recovery_report_file_action_preview",
        fake_preview,
    )

    _assert_action_error(("session-001",), archive_root, output_root)

    assert destination.read_text(encoding="utf-8") == "late private report"


def test_action_source_stays_narrow_and_avoids_forbidden_surfaces() -> None:
    source = inspect.getsource(action)

    assert "build_stored_session_window_recovery_report_file_action_preview" in source
    assert "write_stored_session_window_recovery_report_file" in source
    assert "stored-session-window-recovery-report.md" in source
    for forbidden_fragment in (
        "build_stored_session_window_recovery_report_file_verification",
        "build_stored_session_window_recovery_report_file_inventory",
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
        "threading",
        "Timer",
        "asyncio",
        "gate d",
        "product promise",
    ):
        assert forbidden_fragment not in source
