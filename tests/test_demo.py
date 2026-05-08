from __future__ import annotations

import json
import threading
from pathlib import Path

from async_scholar.demo import (
    FixtureSessionLifecycleController,
    FixtureSessionWorker,
    SessionStatusSnapshot,
    run_fixture_demo,
)

FIXTURE_PATH = Path("tests/fixtures/transcripts/attendance_roll_call.jsonl")
PRIVATE_TRANSCRIPT_SNIPPETS = (
    "Good morning, everyone. I am going to take attendance",
    "When I call your name, please say present",
    "Here, professor.",
)
FORBIDDEN_STATUS_ATTRIBUTES = (
    "segments",
    "events",
    "alerts",
    "alert_payloads",
    "source_segment_ids",
    "source_segment_id",
    "fixture_path",
    "output_root",
    "raw_audio_path",
    "recording_path",
    "private_recording",
    "secrets",
    "auth_state",
    "browser_state",
    "model_path",
    "generated_media",
    "scheduler_state",
    "worker_state",
    "worker_thread",
    "thread",
    "exception",
    "traceback",
    "ui_state",
)
FORBIDDEN_STATUS_TEXT = (
    *PRIVATE_TRANSCRIPT_SNIPPETS,
    "source_segment_id",
    "requires_confirmation",
    "alert payload",
    "microphone.wav",
    "raw_audio",
    "private_recording",
    ".env",
    "cookie",
    "token",
    "auth",
    "browser",
    "model_path",
    "generated_media",
    "scheduler",
    "worker",
    "thread",
    "exception",
    "traceback",
    "nicegui",
)


def test_run_fixture_demo_writes_expected_artifacts(tmp_path) -> None:
    result = run_fixture_demo(FIXTURE_PATH, output_root=tmp_path)

    output_dir = tmp_path / "fixture_attendance_roll_call"
    assert result.session_id == "fixture:attendance_roll_call"
    assert result.segment_count == 5
    assert result.event_count == 2
    assert result.artifact_paths.output_dir == output_dir
    assert result.artifact_paths.events_path == output_dir / "events.jsonl"
    assert result.artifact_paths.alerts_path == output_dir / "alerts.log"
    assert result.artifact_paths.reviewer_path == output_dir / "reviewer.md"

    event_lines = result.artifact_paths.events_path.read_text(
        encoding="utf-8"
    ).splitlines()
    alert_lines = result.artifact_paths.alerts_path.read_text(
        encoding="utf-8"
    ).splitlines()
    reviewer = result.artifact_paths.reviewer_path.read_text(encoding="utf-8")

    assert len(event_lines) == 2
    assert len(alert_lines) == 2
    assert json.loads(event_lines[0])["event_type"] == "attendance_prompt"
    assert json.loads(alert_lines[0])["requires_confirmation"] is True
    assert "Good morning, everyone. I am going to take attendance" in reviewer
    assert "When I call your name, please say present" in reviewer
    assert "Here, professor." not in reviewer


def test_run_fixture_demo_exposes_safe_status_snapshot(tmp_path) -> None:
    result = run_fixture_demo(FIXTURE_PATH, output_root=tmp_path)
    snapshot = result.status_snapshot

    assert isinstance(snapshot, SessionStatusSnapshot)
    assert snapshot.session_id == "fixture:attendance_roll_call"
    assert snapshot.source_kind == "fixture_demo"
    assert snapshot.run_status == "completed"
    assert snapshot.segment_count == 5
    assert snapshot.event_count == 2
    assert snapshot.artifact_paths == result.artifact_paths
    assert snapshot.artifact_paths.output_dir == result.artifact_paths.output_dir
    assert snapshot.artifact_paths.events_path == result.artifact_paths.events_path
    assert snapshot.artifact_paths.alerts_path == result.artifact_paths.alerts_path
    assert snapshot.artifact_paths.reviewer_path == result.artifact_paths.reviewer_path


def test_status_snapshot_keeps_private_contents_out_of_contract(tmp_path) -> None:
    snapshot = run_fixture_demo(FIXTURE_PATH, output_root=tmp_path).status_snapshot

    _assert_status_snapshot_is_private(snapshot)


def test_fixture_session_lifecycle_initial_status_is_safe(tmp_path) -> None:
    controller = FixtureSessionLifecycleController(FIXTURE_PATH, output_root=tmp_path)

    snapshot = controller.status()

    assert snapshot.session_id == "fixture_demo"
    assert snapshot.source_kind == "fixture_demo"
    assert snapshot.run_status == "not_started"
    assert snapshot.segment_count == 0
    assert snapshot.event_count == 0
    assert snapshot.artifact_paths is None
    _assert_status_snapshot_is_private(snapshot)


def test_fixture_session_lifecycle_start_reaches_completed_status(tmp_path) -> None:
    controller = FixtureSessionLifecycleController(FIXTURE_PATH, output_root=tmp_path)

    snapshot = controller.start()

    assert snapshot.session_id == "fixture:attendance_roll_call"
    assert snapshot.source_kind == "fixture_demo"
    assert snapshot.run_status == "completed"
    assert snapshot.segment_count == 5
    assert snapshot.event_count == 2
    assert snapshot.artifact_paths is not None
    assert snapshot.artifact_paths.output_dir == (
        tmp_path / "fixture_attendance_roll_call"
    )
    assert snapshot.artifact_paths.events_path.exists()
    assert snapshot.artifact_paths.alerts_path.exists()
    assert snapshot.artifact_paths.reviewer_path.exists()
    _assert_status_snapshot_is_private(snapshot)


def test_fixture_session_lifecycle_status_reads_are_idempotent(tmp_path) -> None:
    controller = FixtureSessionLifecycleController(FIXTURE_PATH, output_root=tmp_path)

    started_snapshot = controller.start()
    first_status = controller.status()
    second_status = controller.status()

    assert first_status == started_snapshot
    assert second_status == first_status

    assert started_snapshot.artifact_paths is not None
    reviewer_path = started_snapshot.artifact_paths.reviewer_path
    reviewer_text = reviewer_path.read_text(encoding="utf-8")
    reviewer_path.write_text(f"{reviewer_text}\nlocal sentinel", encoding="utf-8")

    assert controller.start() == started_snapshot
    assert reviewer_path.read_text(encoding="utf-8").endswith("\nlocal sentinel")


def test_fixture_session_lifecycle_stop_without_start_is_idempotent(tmp_path) -> None:
    controller = FixtureSessionLifecycleController(FIXTURE_PATH, output_root=tmp_path)

    stopped_snapshot = controller.stop()

    assert stopped_snapshot.session_id == "fixture_demo"
    assert stopped_snapshot.source_kind == "fixture_demo"
    assert stopped_snapshot.run_status == "stopped"
    assert stopped_snapshot.segment_count == 0
    assert stopped_snapshot.event_count == 0
    assert stopped_snapshot.artifact_paths is None
    assert controller.status() == stopped_snapshot
    assert controller.stop() == stopped_snapshot
    assert controller.start() == stopped_snapshot
    assert not (tmp_path / "fixture_attendance_roll_call").exists()
    _assert_status_snapshot_is_private(stopped_snapshot)


def test_fixture_session_lifecycle_stop_preserves_completed_status(tmp_path) -> None:
    controller = FixtureSessionLifecycleController(FIXTURE_PATH, output_root=tmp_path)
    completed_snapshot = controller.start()

    stopped_snapshot = controller.stop()

    assert stopped_snapshot == completed_snapshot
    assert stopped_snapshot.run_status == "completed"
    assert controller.status() == completed_snapshot
    _assert_status_snapshot_is_private(stopped_snapshot)


def test_fixture_session_worker_initial_status_is_safe(tmp_path) -> None:
    worker = FixtureSessionWorker(FIXTURE_PATH, output_root=tmp_path)

    snapshot = worker.status()

    assert isinstance(snapshot, SessionStatusSnapshot)
    assert snapshot.session_id == "fixture_demo"
    assert snapshot.source_kind == "fixture_demo"
    assert snapshot.run_status == "not_started"
    assert snapshot.segment_count == 0
    assert snapshot.event_count == 0
    assert snapshot.artifact_paths is None
    _assert_status_snapshot_is_private(snapshot)


def test_fixture_session_worker_running_and_completed_transition(
    tmp_path_factory,
    monkeypatch,
) -> None:
    output_root = tmp_path_factory.mktemp("session-output")
    entered = threading.Event()
    release = threading.Event()
    original_start = FixtureSessionLifecycleController.start

    def controlled_start(self: FixtureSessionLifecycleController):
        entered.set()
        if not release.wait(timeout=5):
            raise RuntimeError("worker test release was not signaled")
        return original_start(self)

    monkeypatch.setattr(
        FixtureSessionLifecycleController,
        "start",
        controlled_start,
    )
    worker = FixtureSessionWorker(FIXTURE_PATH, output_root=output_root)

    started_snapshot = worker.start()
    assert started_snapshot.run_status == "running"
    assert started_snapshot.artifact_paths is None
    _assert_status_snapshot_is_private(started_snapshot)

    _wait_for_event(entered, "worker thread did not enter the controller")
    running_snapshot = worker.status()
    assert running_snapshot.run_status == "running"
    assert running_snapshot.artifact_paths is None
    assert not (output_root / "fixture_attendance_roll_call").exists()
    _assert_status_snapshot_is_private(running_snapshot)

    release.set()
    completed_snapshot = worker.join(timeout=5)

    assert completed_snapshot.session_id == "fixture:attendance_roll_call"
    assert completed_snapshot.source_kind == "fixture_demo"
    assert completed_snapshot.run_status == "completed"
    assert completed_snapshot.segment_count == 5
    assert completed_snapshot.event_count == 2
    assert completed_snapshot.artifact_paths is not None
    assert completed_snapshot.artifact_paths.output_dir == (
        output_root / "fixture_attendance_roll_call"
    )
    assert completed_snapshot.artifact_paths.events_path.exists()
    assert completed_snapshot.artifact_paths.alerts_path.exists()
    assert completed_snapshot.artifact_paths.reviewer_path.exists()
    _assert_status_snapshot_is_private(completed_snapshot)


def test_fixture_session_worker_start_is_idempotent_while_running(
    tmp_path_factory,
    monkeypatch,
) -> None:
    output_root = tmp_path_factory.mktemp("session-output")
    entered = threading.Event()
    release = threading.Event()
    call_count = 0
    call_count_lock = threading.Lock()
    original_start = FixtureSessionLifecycleController.start

    def controlled_start(self: FixtureSessionLifecycleController):
        nonlocal call_count
        with call_count_lock:
            call_count += 1
        entered.set()
        if not release.wait(timeout=5):
            raise RuntimeError("worker test release was not signaled")
        return original_start(self)

    monkeypatch.setattr(
        FixtureSessionLifecycleController,
        "start",
        controlled_start,
    )
    worker = FixtureSessionWorker(FIXTURE_PATH, output_root=output_root)

    first_snapshot = worker.start()
    _wait_for_event(entered, "worker thread did not enter the controller")
    second_snapshot = worker.start()

    assert first_snapshot.run_status == "running"
    assert second_snapshot.run_status == "running"
    with call_count_lock:
        assert call_count == 1

    release.set()
    completed_snapshot = worker.join(timeout=5)

    assert completed_snapshot.run_status == "completed"
    assert worker.start() == completed_snapshot
    with call_count_lock:
        assert call_count == 1


def test_fixture_session_worker_stop_without_start_prevents_artifacts(tmp_path) -> None:
    worker = FixtureSessionWorker(FIXTURE_PATH, output_root=tmp_path)

    stopped_snapshot = worker.stop()

    assert stopped_snapshot.session_id == "fixture_demo"
    assert stopped_snapshot.source_kind == "fixture_demo"
    assert stopped_snapshot.run_status == "stopped"
    assert stopped_snapshot.segment_count == 0
    assert stopped_snapshot.event_count == 0
    assert stopped_snapshot.artifact_paths is None
    assert worker.status() == stopped_snapshot
    assert worker.stop() == stopped_snapshot
    assert worker.start() == stopped_snapshot
    assert worker.join(timeout=0) == stopped_snapshot
    assert not (tmp_path / "fixture_attendance_roll_call").exists()
    _assert_status_snapshot_is_private(stopped_snapshot)


def test_fixture_session_worker_stop_preserves_completed_status(
    tmp_path_factory,
) -> None:
    output_root = tmp_path_factory.mktemp("session-output")
    worker = FixtureSessionWorker(FIXTURE_PATH, output_root=output_root)
    worker.start()
    completed_snapshot = worker.join(timeout=5)

    stopped_snapshot = worker.stop()

    assert stopped_snapshot == completed_snapshot
    assert stopped_snapshot.run_status == "completed"
    assert worker.status() == completed_snapshot
    _assert_status_snapshot_is_private(stopped_snapshot)


def test_fixture_session_worker_failure_status_is_sanitized(
    tmp_path,
    monkeypatch,
) -> None:
    def failing_start(self: FixtureSessionLifecycleController) -> None:
        raise RuntimeError(
            "Good morning, everyone. source_segment_id token traceback "
            "tests/fixtures/transcripts/attendance_roll_call.jsonl"
        )

    monkeypatch.setattr(
        FixtureSessionLifecycleController,
        "start",
        failing_start,
    )
    worker = FixtureSessionWorker(FIXTURE_PATH, output_root=tmp_path)

    started_snapshot = worker.start()
    failed_snapshot = worker.join(timeout=5)

    assert started_snapshot.run_status == "running"
    assert failed_snapshot.session_id == "fixture_demo"
    assert failed_snapshot.source_kind == "fixture_demo"
    assert failed_snapshot.run_status == "failed"
    assert failed_snapshot.segment_count == 0
    assert failed_snapshot.event_count == 0
    assert failed_snapshot.artifact_paths is None
    assert worker.status() == failed_snapshot
    assert worker.start() == failed_snapshot
    assert not (tmp_path / "fixture_attendance_roll_call").exists()
    _assert_status_snapshot_is_private(started_snapshot)
    _assert_status_snapshot_is_private(failed_snapshot)


def _wait_for_event(event: threading.Event, message: str) -> None:
    assert event.wait(timeout=5), message


def _assert_status_snapshot_is_private(snapshot: SessionStatusSnapshot) -> None:
    assert set(SessionStatusSnapshot.__dataclass_fields__) == {
        "session_id",
        "source_kind",
        "run_status",
        "segment_count",
        "event_count",
        "artifact_paths",
    }
    for attribute_name in FORBIDDEN_STATUS_ATTRIBUTES:
        assert not hasattr(snapshot, attribute_name)

    safe_status_values = {
        "session_id": snapshot.session_id,
        "source_kind": snapshot.source_kind,
        "run_status": snapshot.run_status,
        "segment_count": snapshot.segment_count,
        "event_count": snapshot.event_count,
    }
    safe_status_text = json.dumps(safe_status_values, sort_keys=True)

    artifact_path_text = ""
    if snapshot.artifact_paths is not None:
        artifact_path_text = json.dumps(
            {
                "output_dir": str(snapshot.artifact_paths.output_dir),
                "events_path": str(snapshot.artifact_paths.events_path),
                "alerts_path": str(snapshot.artifact_paths.alerts_path),
                "reviewer_path": str(snapshot.artifact_paths.reviewer_path),
            },
            sort_keys=True,
        )

    exposed_status_text = f"{safe_status_text}\n{artifact_path_text}"
    for forbidden_text in FORBIDDEN_STATUS_TEXT:
        assert forbidden_text.lower() not in exposed_status_text.lower()
