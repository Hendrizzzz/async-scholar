"""SQLite storage for manually entered course schedules."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, ValidationError

from async_scholar.course_metadata import CourseMetadata
from async_scholar.schedule_config import ScheduleConfig

COURSE_SCHEDULE_STORE_ERROR = "course schedule store could not be built"
COURSE_SCHEDULE_SAVE_ERROR = "course schedule could not be saved"
COURSE_SCHEDULE_LOAD_ERROR = "course schedule could not be loaded"
COURSE_SCHEDULE_SUMMARY_ERROR = "course schedule summary could not be built"

_COURSES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS courses (
    course_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    instructor_name TEXT,
    meeting_url TEXT,
    meeting_label TEXT
)
"""

_CLASS_TIMES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS class_times (
    course_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    day_of_week TEXT NOT NULL,
    local_start_time TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL,
    timezone_name TEXT,
    meeting_label TEXT,
    PRIMARY KEY (course_id, position),
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE
)
"""


class StoredCourseSchedule(BaseModel):
    """Immutable loaded schedule record with a redacted public summary."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    course_id: StrictStr
    class_time_count: StrictInt = Field(ge=1)
    course_metadata: CourseMetadata = Field(repr=False)
    schedule_config: ScheduleConfig = Field(repr=False)

    def to_safe_summary(self) -> dict[str, object]:
        return {
            "course_id": self.course_id,
            "class_time_count": self.class_time_count,
        }

    def safe_summary(self) -> dict[str, object]:
        return self.to_safe_summary()


def initialize_course_schedule_store(db_path: str | Path) -> None:
    """Create the course schedule tables at an explicit local SQLite path."""

    try:
        safe_db_path = _validate_db_path(db_path)
        with sqlite3.connect(safe_db_path) as connection:
            _configure_connection(connection)
            _create_schema(connection)
    except (OSError, RuntimeError, TypeError, sqlite3.Error, ValueError):
        raise ValueError(COURSE_SCHEDULE_STORE_ERROR) from None


def save_course_schedule(
    db_path: str | Path,
    course_metadata: CourseMetadata,
    schedule_config: ScheduleConfig,
) -> StoredCourseSchedule:
    """Persist one validated course schedule into the explicit local store."""

    try:
        safe_db_path = _validate_db_path(db_path)
        safe_course_metadata = _revalidate_course_metadata(course_metadata)
        safe_schedule_config = _revalidate_schedule_config(schedule_config)
        if safe_course_metadata.course_id != safe_schedule_config.course_id:
            raise ValueError("course IDs must match")

        with sqlite3.connect(safe_db_path) as connection:
            _configure_connection(connection)
            _create_schema(connection)
            with connection:
                connection.execute(
                    """
                    INSERT INTO courses (
                        course_id,
                        title,
                        instructor_name,
                        meeting_url,
                        meeting_label
                    )
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(course_id) DO UPDATE SET
                        title = excluded.title,
                        instructor_name = excluded.instructor_name,
                        meeting_url = excluded.meeting_url,
                        meeting_label = excluded.meeting_label
                    """,
                    (
                        safe_course_metadata.course_id,
                        safe_course_metadata.title,
                        safe_course_metadata.instructor_name,
                        safe_course_metadata.meeting_url,
                        safe_course_metadata.meeting_label,
                    ),
                )
                connection.execute(
                    "DELETE FROM class_times WHERE course_id = ?",
                    (safe_course_metadata.course_id,),
                )
                for position, class_time in enumerate(safe_schedule_config.class_times):
                    connection.execute(
                        """
                        INSERT INTO class_times (
                            course_id,
                            position,
                            day_of_week,
                            local_start_time,
                            duration_minutes,
                            timezone_name,
                            meeting_label
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            safe_course_metadata.course_id,
                            position,
                            class_time.day_of_week,
                            class_time.local_start_time,
                            class_time.duration_minutes,
                            class_time.timezone_name,
                            class_time.meeting_label,
                        ),
                    )
        return StoredCourseSchedule(
            course_id=safe_course_metadata.course_id,
            class_time_count=len(safe_schedule_config.class_times),
            course_metadata=safe_course_metadata,
            schedule_config=safe_schedule_config,
        )
    except (
        OSError,
        RuntimeError,
        TypeError,
        ValidationError,
        sqlite3.Error,
        ValueError,
    ):
        raise ValueError(COURSE_SCHEDULE_SAVE_ERROR) from None


def load_course_schedule(db_path: str | Path, course_id: str) -> StoredCourseSchedule:
    """Load one course schedule by safe course ID from the explicit local store."""

    try:
        safe_db_path = _validate_db_path(db_path)
        safe_course_id = _normalize_course_id(course_id)
        with sqlite3.connect(safe_db_path) as connection:
            connection.row_factory = sqlite3.Row
            _configure_connection(connection)
            _create_schema(connection)
            course_row = connection.execute(
                """
                SELECT
                    course_id,
                    title,
                    instructor_name,
                    meeting_url,
                    meeting_label
                FROM courses
                WHERE course_id = ?
                """,
                (safe_course_id,),
            ).fetchone()
            if course_row is None:
                raise ValueError("course schedule is missing")

            class_time_rows = connection.execute(
                """
                SELECT
                    day_of_week,
                    local_start_time,
                    duration_minutes,
                    timezone_name,
                    meeting_label
                FROM class_times
                WHERE course_id = ?
                ORDER BY position
                """,
                (safe_course_id,),
            ).fetchall()
            if not class_time_rows:
                raise ValueError("course schedule has no class times")

        course_metadata = CourseMetadata(
            course_id=course_row["course_id"],
            title=course_row["title"],
            instructor_name=course_row["instructor_name"],
            meeting_url=course_row["meeting_url"],
            meeting_label=course_row["meeting_label"],
        )
        schedule_config = ScheduleConfig(
            course_id=course_row["course_id"],
            class_times=[
                {
                    "day_of_week": row["day_of_week"],
                    "local_start_time": row["local_start_time"],
                    "duration_minutes": row["duration_minutes"],
                    "timezone_name": row["timezone_name"],
                    "meeting_label": row["meeting_label"],
                }
                for row in class_time_rows
            ],
        )
        return StoredCourseSchedule(
            course_id=course_metadata.course_id,
            class_time_count=len(schedule_config.class_times),
            course_metadata=course_metadata,
            schedule_config=schedule_config,
        )
    except (
        OSError,
        RuntimeError,
        TypeError,
        ValidationError,
        sqlite3.Error,
        ValueError,
    ):
        raise ValueError(COURSE_SCHEDULE_LOAD_ERROR) from None


def load_course_schedule_safe_summary(
    db_path: str | Path,
    course_id: str,
) -> dict[str, object]:
    """Read one stored schedule summary without creating or modifying the store."""

    try:
        safe_db_path = _validate_existing_db_path(db_path)
        safe_course_id = _normalize_course_id(course_id)
        read_only_uri = f"{safe_db_path.resolve(strict=True).as_uri()}?mode=ro"
        with sqlite3.connect(read_only_uri, uri=True) as connection:
            connection.row_factory = sqlite3.Row
            _configure_connection(connection)
            course_row = connection.execute(
                """
                SELECT
                    course_id,
                    title,
                    instructor_name,
                    meeting_url,
                    meeting_label
                FROM courses
                WHERE course_id = ?
                """,
                (safe_course_id,),
            ).fetchone()
            if course_row is None:
                raise ValueError("course schedule is missing")

            class_time_rows = connection.execute(
                """
                SELECT
                    day_of_week,
                    local_start_time,
                    duration_minutes,
                    timezone_name,
                    meeting_label
                FROM class_times
                WHERE course_id = ?
                ORDER BY position
                """,
                (safe_course_id,),
            ).fetchall()
            if not class_time_rows:
                raise ValueError("course schedule has no class times")

        course_metadata = CourseMetadata(
            course_id=course_row["course_id"],
            title=course_row["title"],
            instructor_name=course_row["instructor_name"],
            meeting_url=course_row["meeting_url"],
            meeting_label=course_row["meeting_label"],
        )
        schedule_config = ScheduleConfig(
            course_id=course_row["course_id"],
            class_times=[
                {
                    "day_of_week": row["day_of_week"],
                    "local_start_time": row["local_start_time"],
                    "duration_minutes": row["duration_minutes"],
                    "timezone_name": row["timezone_name"],
                    "meeting_label": row["meeting_label"],
                }
                for row in class_time_rows
            ],
        )
        return StoredCourseSchedule(
            course_id=course_metadata.course_id,
            class_time_count=len(schedule_config.class_times),
            course_metadata=course_metadata,
            schedule_config=schedule_config,
        ).safe_summary()
    except (
        OSError,
        RuntimeError,
        TypeError,
        ValidationError,
        sqlite3.Error,
        ValueError,
    ):
        raise ValueError(COURSE_SCHEDULE_SUMMARY_ERROR) from None


def _validate_db_path(db_path: str | Path) -> Path:
    if not isinstance(db_path, (str, Path)):
        raise ValueError("db_path must be an explicit local path")
    db_path_text = str(db_path)
    if db_path_text != db_path_text.strip() or not db_path_text:
        raise ValueError("db_path must be an explicit local path")
    if any(ord(character) < 32 or ord(character) == 127 for character in db_path_text):
        raise ValueError("db_path must be a safe local path")

    normalized_text = "".join(
        "\\" if character == "/" else character for character in db_path_text
    )
    lowered_text = db_path_text.lower()
    if (
        normalized_text.startswith("\\\\")
        or lowered_text == ":memory:"
        or lowered_text.startswith("file:")
        or "://" in lowered_text
    ):
        raise ValueError("db_path must be a local filesystem path")

    candidate = Path(db_path)
    if candidate.exists() and (candidate.is_dir() or candidate.is_symlink()):
        raise ValueError("db_path must be a writable local database file")
    parent = candidate.parent
    if not parent.exists() or not parent.is_dir() or parent.is_symlink():
        raise ValueError("db_path parent must be a local directory")
    return candidate


def _validate_existing_db_path(db_path: str | Path) -> Path:
    candidate = _validate_db_path(db_path)
    if not candidate.exists() or not candidate.is_file() or candidate.is_symlink():
        raise ValueError("db_path must be an existing local database file")
    return candidate


def _configure_connection(connection: sqlite3.Connection) -> None:
    connection.execute("PRAGMA foreign_keys = ON")


def _create_schema(connection: sqlite3.Connection) -> None:
    connection.execute(_COURSES_TABLE_SQL)
    connection.execute(_CLASS_TIMES_TABLE_SQL)


def _model_to_dict(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _revalidate_course_metadata(course_metadata: CourseMetadata) -> CourseMetadata:
    if type(course_metadata) is not CourseMetadata:
        raise ValueError("course_metadata must be CourseMetadata")
    return CourseMetadata(**_model_to_dict(course_metadata))


def _revalidate_schedule_config(schedule_config: ScheduleConfig) -> ScheduleConfig:
    if type(schedule_config) is not ScheduleConfig:
        raise ValueError("schedule_config must be ScheduleConfig")
    return ScheduleConfig(**_model_to_dict(schedule_config))


def _normalize_course_id(course_id: str) -> str:
    return CourseMetadata(course_id=course_id, title="Course").course_id
