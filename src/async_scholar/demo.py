"""Fixture demo orchestration for the early local pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from async_scholar.artifacts import ArtifactPaths, write_session_artifacts
from async_scholar.fixtures import load_transcript_fixture
from async_scholar.rules import detect_events


@dataclass(frozen=True)
class SessionStatusSnapshot:
    session_id: str
    source_kind: str
    run_status: str
    segment_count: int
    event_count: int
    artifact_paths: ArtifactPaths | None


@dataclass(frozen=True)
class FixtureDemoResult:
    session_id: str
    segment_count: int
    event_count: int
    artifact_paths: ArtifactPaths

    @property
    def status_snapshot(self) -> SessionStatusSnapshot:
        return SessionStatusSnapshot(
            session_id=self.session_id,
            source_kind="fixture_demo",
            run_status="completed",
            segment_count=self.segment_count,
            event_count=self.event_count,
            artifact_paths=self.artifact_paths,
        )


class FixtureSessionLifecycleController:
    """Synchronous fixture-backed lifecycle surface for Gate C prep."""

    def __init__(
        self,
        fixture_path: str | Path,
        *,
        output_root: str | Path = Path("data") / "sessions",
    ) -> None:
        self._fixture_path = Path(fixture_path)
        self._output_root = Path(output_root)
        self._result: FixtureDemoResult | None = None
        self._run_status = "not_started"

    def start(self) -> SessionStatusSnapshot:
        if self._result is not None or self._run_status == "stopped":
            return self.status()

        self._result = run_fixture_demo(
            self._fixture_path,
            output_root=self._output_root,
        )
        self._run_status = "completed"
        return self.status()

    def status(self) -> SessionStatusSnapshot:
        if self._result is not None:
            return self._result.status_snapshot

        return SessionStatusSnapshot(
            session_id="fixture_demo",
            source_kind="fixture_demo",
            run_status=self._run_status,
            segment_count=0,
            event_count=0,
            artifact_paths=None,
        )

    def stop(self) -> SessionStatusSnapshot:
        if self._result is None:
            self._run_status = "stopped"
        return self.status()


def run_fixture_demo(
    fixture_path: str | Path,
    *,
    output_root: str | Path = Path("data") / "sessions",
) -> FixtureDemoResult:
    fixture = Path(fixture_path)
    segments = load_transcript_fixture(fixture)
    events = detect_events(segments)
    session_id = segments[0].session_id if segments else f"fixture:{fixture.stem}"
    artifact_paths = write_session_artifacts(
        session_id=session_id,
        segments=segments,
        events=events,
        output_root=output_root,
    )

    return FixtureDemoResult(
        session_id=session_id,
        segment_count=len(segments),
        event_count=len(events),
        artifact_paths=artifact_paths,
    )


__all__ = [
    "FixtureDemoResult",
    "FixtureSessionLifecycleController",
    "SessionStatusSnapshot",
    "run_fixture_demo",
]
