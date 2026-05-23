from __future__ import annotations

import inspect
import sqlite3
from pathlib import Path

import pytest
from pydantic import ValidationError

from async_scholar import schedule_store
from async_scholar.course_metadata import CourseMetadata
from async_scholar.schedule_config import ScheduleConfig
from async_scholar.schedule_store import (
    COURSE_SCHEDULE_DUE_LIST_ERROR,
    COURSE_SCHEDULE_LIST_ERROR,
    COURSE_SCHEDULE_LOAD_ERROR,
    COURSE_SCHEDULE_SAVE_ERROR,
    COURSE_SCHEDULE_STORE_ERROR,
    COURSE_SCHEDULE_SUMMARY_ERROR,
    StoredCourseSchedule,
    initialize_course_schedule_store,
    list_course_schedule_due_list_inputs,
    list_course_schedule_safe_summaries,
    load_course_schedule,
    load_course_schedule_read_only,
    load_course_schedule_safe_summary,
    save_course_schedule,
)


def _private_meeting_url() -> str:
    return "https://meet.example.edu/class-room?token=private"


def _course_metadata(course_id: str = "cs101") -> CourseMetadata:
    return CourseMetadata(
        course_id=course_id,
        title="Confidential Systems",
        instructor_name="Dr. Private",
        meeting_url=_private_meeting_url(),
        meeting_label="Private lecture",
    )


def _schedule_config(
    course_id: str = "cs101",
    *,
    second_time: bool = True,
) -> ScheduleConfig:
    class_times: list[dict[str, object]] = [
        {
            "day_of_week": "monday",
            "local_start_time": "09:00",
            "duration_minutes": 75,
            "timezone_name": "Asia/Manila",
            "meeting_label": "Private lecture",
        }
    ]
    if second_time:
        class_times.append(
            {
                "day_of_week": "wednesday",
                "local_start_time": "13:30",
                "duration_minutes": 90,
                "timezone_name": "Asia/Manila",
                "meeting_label": "Private lab",
            }
        )
    return ScheduleConfig(course_id=course_id, class_times=class_times)


def test_initialize_save_and_load_course_schedule_round_trip(tmp_path: Path) -> None:
    db_path = tmp_path / "schedule.sqlite"

    initialize_course_schedule_store(db_path)
    saved = save_course_schedule(db_path, _course_metadata(), _schedule_config())
    loaded = load_course_schedule(db_path, "cs101")

    assert db_path.is_file()
    assert saved.safe_summary() == {"course_id": "cs101", "class_time_count": 2}
    assert loaded.safe_summary() == {"course_id": "cs101", "class_time_count": 2}
    assert loaded.to_safe_summary() == loaded.safe_summary()
    assert loaded.course_metadata.course_id == "cs101"
    assert loaded.course_metadata.meeting_url is not None
    assert loaded.schedule_config.class_times[0].day_of_week == "monday"
    assert loaded.schedule_config.class_times[1].local_start_time == "13:30"

    public_text = f"{loaded!r} {loaded.safe_summary()}"
    for forbidden_fragment in (
        "meeting_url",
        "meet.example",
        "token",
        "private",
        "confidential",
        "instructor",
        "dr.",
        "lecture",
        "lab",
        "auth",
        "cookie",
        "profile",
        "transcript",
        "audio",
    ):
        assert forbidden_fragment not in public_text.lower()


def test_load_returns_immutable_record_with_redacted_summary(tmp_path: Path) -> None:
    db_path = tmp_path / "schedule.sqlite"
    save_course_schedule(db_path, _course_metadata(), _schedule_config())

    loaded = load_course_schedule(db_path, "cs101")

    with pytest.raises((TypeError, ValidationError)):
        loaded.course_id = "math101"
    assert isinstance(loaded, StoredCourseSchedule)
    assert set(loaded.safe_summary()) == {"course_id", "class_time_count"}


def test_load_course_schedule_safe_summary_is_read_only_and_redacted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    save_course_schedule(db_path, _course_metadata(), _schedule_config())
    real_connect = schedule_store.sqlite3.connect
    connection_call: dict[str, object] = {}

    def checking_connect(database: object, *args: object, **kwargs: object) -> object:
        connection_call["database"] = str(database)
        connection_call["uri"] = kwargs.get("uri")
        return real_connect(database, *args, **kwargs)

    monkeypatch.setattr(schedule_store.sqlite3, "connect", checking_connect)

    summary = load_course_schedule_safe_summary(db_path, "cs101")

    assert summary == {"course_id": "cs101", "class_time_count": 2}
    assert connection_call["uri"] is True
    assert str(connection_call["database"]).endswith("?mode=ro")
    public_text = str(summary).lower()
    for forbidden_fragment in (
        "meeting",
        "meet.example",
        "token",
        "private",
        "confidential",
        "instructor",
        "dr.",
        "lecture",
        "lab",
        "timezone",
        "auth",
        "cookie",
        "profile",
        "transcript",
        "audio",
    ):
        assert forbidden_fragment not in public_text


def test_load_course_schedule_read_only_uses_read_only_uri_and_validates_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    save_course_schedule(db_path, _course_metadata(), _schedule_config())
    real_connect = schedule_store.sqlite3.connect
    connection_call: dict[str, object] = {}

    def checking_connect(database: object, *args: object, **kwargs: object) -> object:
        connection_call["database"] = str(database)
        connection_call["uri"] = kwargs.get("uri")
        return real_connect(database, *args, **kwargs)

    monkeypatch.setattr(schedule_store.sqlite3, "connect", checking_connect)

    loaded = load_course_schedule_read_only(db_path, "cs101")

    assert loaded.safe_summary() == {"course_id": "cs101", "class_time_count": 2}
    assert loaded.course_metadata.meeting_url == _private_meeting_url()
    assert loaded.schedule_config.class_times[1].day_of_week == "wednesday"
    assert connection_call["uri"] is True
    assert str(connection_call["database"]).endswith("?mode=ro")


def test_list_course_schedule_safe_summaries_is_read_only_sorted_and_redacted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    save_course_schedule(
        db_path,
        _course_metadata("math101"),
        _schedule_config("math101", second_time=False),
    )
    save_course_schedule(db_path, _course_metadata("cs101"), _schedule_config())
    real_connect = schedule_store.sqlite3.connect
    connection_call: dict[str, object] = {}

    def checking_connect(database: object, *args: object, **kwargs: object) -> object:
        connection_call["database"] = str(database)
        connection_call["uri"] = kwargs.get("uri")
        return real_connect(database, *args, **kwargs)

    monkeypatch.setattr(schedule_store.sqlite3, "connect", checking_connect)

    summary = list_course_schedule_safe_summaries(db_path)

    assert summary == {
        "course_count": 2,
        "courses": [
            {"course_id": "cs101", "class_time_count": 2},
            {"course_id": "math101", "class_time_count": 1},
        ],
    }
    assert connection_call["uri"] is True
    assert str(connection_call["database"]).endswith("?mode=ro")
    public_text = str(summary).lower()
    for forbidden_fragment in (
        "meeting",
        "meet.example",
        "token",
        "private",
        "confidential",
        "instructor",
        "dr.",
        "lecture",
        "lab",
        "timezone",
        "duration",
        "auth",
        "cookie",
        "profile",
        "transcript",
        "audio",
        "browser",
    ):
        assert forbidden_fragment not in public_text


def test_list_course_schedule_safe_summaries_allows_empty_existing_store(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    initialize_course_schedule_store(db_path)

    summary = list_course_schedule_safe_summaries(db_path)

    assert summary == {"course_count": 0, "courses": []}


def test_list_course_schedule_due_list_inputs_is_read_only_sorted_and_redacted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    save_course_schedule(
        db_path,
        _course_metadata("math101"),
        _schedule_config("math101", second_time=False),
    )
    save_course_schedule(db_path, _course_metadata("cs101"), _schedule_config())
    real_connect = schedule_store.sqlite3.connect
    connection_call: dict[str, object] = {}

    def checking_connect(database: object, *args: object, **kwargs: object) -> object:
        connection_call["database"] = str(database)
        connection_call["uri"] = kwargs.get("uri")
        return real_connect(database, *args, **kwargs)

    monkeypatch.setattr(schedule_store.sqlite3, "connect", checking_connect)

    summary = list_course_schedule_due_list_inputs(db_path)

    assert summary == {
        "course_count": 2,
        "courses": [
            {
                "course_id": "cs101",
                "class_times": [
                    {
                        "selected_class_time_index": 0,
                        "scheduled_day_of_week": "monday",
                        "scheduled_local_start_time": "09:00",
                    },
                    {
                        "selected_class_time_index": 1,
                        "scheduled_day_of_week": "wednesday",
                        "scheduled_local_start_time": "13:30",
                    },
                ],
            },
            {
                "course_id": "math101",
                "class_times": [
                    {
                        "selected_class_time_index": 0,
                        "scheduled_day_of_week": "monday",
                        "scheduled_local_start_time": "09:00",
                    }
                ],
            },
        ],
    }
    assert connection_call["uri"] is True
    assert str(connection_call["database"]).endswith("?mode=ro")
    public_text = str(summary).lower()
    for forbidden_fragment in (
        "meeting",
        "meet.example",
        "token",
        "private",
        "confidential",
        "instructor",
        "dr.",
        "lecture",
        "lab",
        "timezone",
        "duration",
        "auth",
        "cookie",
        "profile",
        "transcript",
        "audio",
        "browser",
    ):
        assert forbidden_fragment not in public_text


def test_list_course_schedule_due_list_inputs_allows_empty_existing_store(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    initialize_course_schedule_store(db_path)

    summary = list_course_schedule_due_list_inputs(db_path)

    assert summary == {"course_count": 0, "courses": []}


def test_load_course_schedule_safe_summary_rejects_missing_db_without_creating(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "missing-token-secret-auth-profile.sqlite"

    with pytest.raises(ValueError) as exc_info:
        load_course_schedule_safe_summary(db_path, "cs101")

    assert str(exc_info.value) == COURSE_SCHEDULE_SUMMARY_ERROR
    assert not db_path.exists()
    for forbidden_fragment in (
        str(tmp_path).lower(),
        "missing-token",
        "secret",
        "auth",
        "profile",
        "sqlite",
        "traceback",
    ):
        assert forbidden_fragment not in str(exc_info.value).lower()


def test_list_course_schedule_safe_summaries_rejects_missing_db_without_creating(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "missing-token-secret-auth-profile.sqlite"

    with pytest.raises(ValueError) as exc_info:
        list_course_schedule_safe_summaries(db_path)

    assert str(exc_info.value) == COURSE_SCHEDULE_LIST_ERROR
    assert not db_path.exists()
    for forbidden_fragment in (
        str(tmp_path).lower(),
        "missing-token",
        "secret",
        "auth",
        "profile",
        "sqlite",
        "traceback",
    ):
        assert forbidden_fragment not in str(exc_info.value).lower()


def test_list_course_schedule_due_list_inputs_rejects_missing_db_without_creating(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "missing-token-secret-auth-profile.sqlite"

    with pytest.raises(ValueError) as exc_info:
        list_course_schedule_due_list_inputs(db_path)

    assert str(exc_info.value) == COURSE_SCHEDULE_DUE_LIST_ERROR
    assert not db_path.exists()
    for forbidden_fragment in (
        str(tmp_path).lower(),
        "missing-token",
        "secret",
        "auth",
        "profile",
        "sqlite",
        "traceback",
    ):
        assert forbidden_fragment not in str(exc_info.value).lower()


def test_load_course_schedule_safe_summary_sanitizes_missing_course(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    save_course_schedule(db_path, _course_metadata(), _schedule_config())

    with pytest.raises(ValueError) as exc_info:
        load_course_schedule_safe_summary(db_path, "missing-token-secret-auth-profile")

    assert str(exc_info.value) == COURSE_SCHEDULE_SUMMARY_ERROR
    for forbidden_fragment in (
        "missing",
        "token",
        "secret",
        "auth",
        "profile",
        str(tmp_path).lower(),
        "select",
        "sqlite",
        "traceback",
    ):
        assert forbidden_fragment not in str(exc_info.value).lower()


def test_load_course_schedule_safe_summary_sanitizes_malformed_store(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE courses (course_id TEXT PRIMARY KEY)")
        connection.execute("INSERT INTO courses (course_id) VALUES (?)", ("cs101",))

    with pytest.raises(ValueError) as exc_info:
        load_course_schedule_safe_summary(db_path, "cs101")

    assert str(exc_info.value) == COURSE_SCHEDULE_SUMMARY_ERROR
    for forbidden_fragment in (
        str(tmp_path).lower(),
        "class_times",
        "select",
        "sqlite",
        "traceback",
    ):
        assert forbidden_fragment not in str(exc_info.value).lower()


def test_list_course_schedule_safe_summaries_sanitizes_malformed_store(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE courses (
                course_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                instructor_name TEXT,
                meeting_url TEXT,
                meeting_label TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE class_times (
                course_id TEXT NOT NULL,
                position INTEGER NOT NULL,
                day_of_week TEXT NOT NULL,
                local_start_time TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                timezone_name TEXT,
                meeting_label TEXT,
                PRIMARY KEY (course_id, position)
            )
            """
        )
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
            """,
            (
                "cs101",
                "Confidential Systems",
                "Dr. Private",
                _private_meeting_url(),
                "Private lecture",
            ),
        )

    with pytest.raises(ValueError) as exc_info:
        list_course_schedule_safe_summaries(db_path)

    assert str(exc_info.value) == COURSE_SCHEDULE_LIST_ERROR
    for forbidden_fragment in (
        str(tmp_path).lower(),
        "confidential",
        "private",
        "meet.example",
        "token",
        "class_times",
        "select",
        "sqlite",
        "traceback",
    ):
        assert forbidden_fragment not in str(exc_info.value).lower()


def test_list_course_schedule_due_list_inputs_sanitizes_malformed_store(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE courses (
                course_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                instructor_name TEXT,
                meeting_url TEXT,
                meeting_label TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE class_times (
                course_id TEXT NOT NULL,
                position INTEGER NOT NULL,
                day_of_week TEXT NOT NULL,
                local_start_time TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                timezone_name TEXT,
                meeting_label TEXT,
                PRIMARY KEY (course_id, position)
            )
            """
        )
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
            """,
            (
                "cs101",
                "Confidential Systems",
                "Dr. Private",
                _private_meeting_url(),
                "Private lecture",
            ),
        )

    with pytest.raises(ValueError) as exc_info:
        list_course_schedule_due_list_inputs(db_path)

    assert str(exc_info.value) == COURSE_SCHEDULE_DUE_LIST_ERROR
    for forbidden_fragment in (
        str(tmp_path).lower(),
        "confidential",
        "private",
        "meet.example",
        "token",
        "class_times",
        "select",
        "sqlite",
        "traceback",
    ):
        assert forbidden_fragment not in str(exc_info.value).lower()


def test_load_course_schedule_safe_summary_sanitizes_invalid_class_time_rows(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE courses (
                course_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                instructor_name TEXT,
                meeting_url TEXT,
                meeting_label TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE class_times (
                course_id TEXT NOT NULL,
                position INTEGER NOT NULL,
                day_of_week TEXT NOT NULL,
                local_start_time TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                timezone_name TEXT,
                meeting_label TEXT,
                PRIMARY KEY (course_id, position)
            )
            """
        )
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
            """,
            (
                "cs101",
                "Confidential Systems",
                "Dr. Private",
                _private_meeting_url(),
                "Private lecture",
            ),
        )
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
                "cs101",
                0,
                "notaday",
                "99:99",
                -5,
                "Asia/Manila",
                "Private lecture",
            ),
        )

    with pytest.raises(ValueError) as exc_info:
        load_course_schedule_safe_summary(db_path, "cs101")

    assert str(exc_info.value) == COURSE_SCHEDULE_SUMMARY_ERROR
    for forbidden_fragment in (
        str(tmp_path).lower(),
        "notaday",
        "99:99",
        "-5",
        "confidential",
        "private",
        "meet.example",
        "token",
        "traceback",
    ):
        assert forbidden_fragment not in str(exc_info.value).lower()


def test_save_replaces_stale_class_time_rows_deterministically(tmp_path: Path) -> None:
    db_path = tmp_path / "schedule.sqlite"
    save_course_schedule(db_path, _course_metadata(), _schedule_config())

    replacement_config = ScheduleConfig(
        course_id="cs101",
        class_times=[
            {
                "day_of_week": "friday",
                "local_start_time": "14:00",
                "duration_minutes": 45,
            }
        ],
    )
    save_course_schedule(db_path, _course_metadata(), replacement_config)
    loaded = load_course_schedule(db_path, "cs101")

    assert loaded.safe_summary() == {"course_id": "cs101", "class_time_count": 1}
    assert len(loaded.schedule_config.class_times) == 1
    assert loaded.schedule_config.class_times[0].day_of_week == "friday"
    assert loaded.schedule_config.class_times[0].local_start_time == "14:00"
    with sqlite3.connect(db_path) as connection:
        positions = [
            row[0]
            for row in connection.execute(
                "SELECT position FROM class_times ORDER BY position"
            ).fetchall()
        ]
    assert positions == [0]


def test_store_rejects_mismatched_course_ids_with_sanitized_error(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"

    with pytest.raises(ValueError) as exc_info:
        save_course_schedule(
            db_path,
            _course_metadata("cs101"),
            _schedule_config("math101"),
        )

    assert str(exc_info.value) == COURSE_SCHEDULE_SAVE_ERROR
    for forbidden_fragment in ("cs101", "math101", str(tmp_path), "traceback"):
        assert forbidden_fragment not in str(exc_info.value).lower()


def test_load_missing_course_uses_fixed_sanitized_error(tmp_path: Path) -> None:
    db_path = tmp_path / "schedule.sqlite"
    initialize_course_schedule_store(db_path)

    with pytest.raises(ValueError) as exc_info:
        load_course_schedule(db_path, "missing-token-secret-auth-profile")

    assert str(exc_info.value) == COURSE_SCHEDULE_LOAD_ERROR
    for forbidden_fragment in (
        "missing",
        "token",
        "secret",
        "auth",
        "profile",
        str(tmp_path),
        "select",
        "sqlite",
        "traceback",
    ):
        assert forbidden_fragment not in str(exc_info.value).lower()


def test_store_rejects_unsafe_db_paths_before_metadata_probes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    probe_calls: list[str] = []

    def fail_if_probe_runs(self: Path) -> bool:
        probe_calls.append(str(self))
        raise AssertionError("unsafe DB paths must be rejected before metadata probes")

    monkeypatch.setattr(Path, "exists", fail_if_probe_runs)
    monkeypatch.setattr(Path, "is_dir", fail_if_probe_runs)
    monkeypatch.setattr(Path, "is_symlink", fail_if_probe_runs)

    for db_path in (
        "\\\\server\\share\\token-secret-auth-profile.sqlite",
        "//server/share/token-secret-auth-profile.sqlite",
        "file:token-secret-auth-profile.sqlite",
        "https://example.test/token-secret-auth-profile.sqlite",
        ":memory:",
        "",
        "   ",
        "schedule\nsecret.sqlite",
    ):
        with pytest.raises(ValueError) as exc_info:
            initialize_course_schedule_store(db_path)

        assert str(exc_info.value) == COURSE_SCHEDULE_STORE_ERROR
        assert probe_calls == []

        with pytest.raises(ValueError) as list_exc_info:
            list_course_schedule_safe_summaries(db_path)

        assert str(list_exc_info.value) == COURSE_SCHEDULE_LIST_ERROR
        assert probe_calls == []


def test_list_course_schedule_safe_summaries_rejects_directory_and_symlink_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    directory_path = tmp_path / "token-secret-auth-profile-dir"
    directory_path.mkdir()

    with pytest.raises(ValueError) as dir_exc_info:
        list_course_schedule_safe_summaries(directory_path)

    assert str(dir_exc_info.value) == COURSE_SCHEDULE_LIST_ERROR
    for forbidden_fragment in (
        str(tmp_path).lower(),
        "token",
        "secret",
        "auth",
        "profile",
        "traceback",
    ):
        assert forbidden_fragment not in str(dir_exc_info.value).lower()

    def fake_connect(*args: object, **kwargs: object) -> object:
        raise AssertionError("symlink DB paths must be rejected before connect")

    monkeypatch.setattr(schedule_store.sqlite3, "connect", fake_connect)
    monkeypatch.setattr(Path, "exists", lambda self: True)
    monkeypatch.setattr(Path, "is_dir", lambda self: False)
    monkeypatch.setattr(Path, "is_symlink", lambda self: True)

    with pytest.raises(ValueError) as symlink_exc_info:
        list_course_schedule_safe_summaries("token-secret-auth-profile.sqlite")

    assert str(symlink_exc_info.value) == COURSE_SCHEDULE_LIST_ERROR


def test_store_sanitizes_sqlite_and_path_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "schedule.sqlite"

    def fail_connect(db_path: object) -> object:
        raise sqlite3.OperationalError(
            "C:\\Users\\student\\token-secret-auth-profile SELECT *"
        )

    monkeypatch.setattr(schedule_store.sqlite3, "connect", fail_connect)

    checks = (
        (
            lambda: initialize_course_schedule_store(db_path),
            COURSE_SCHEDULE_STORE_ERROR,
        ),
        (
            lambda: save_course_schedule(
                db_path,
                _course_metadata(),
                _schedule_config(),
            ),
            COURSE_SCHEDULE_SAVE_ERROR,
        ),
        (
            lambda: load_course_schedule(db_path, "cs101"),
            COURSE_SCHEDULE_LOAD_ERROR,
        ),
    )
    for action, expected_error in checks:
        with pytest.raises(ValueError) as exc_info:
            action()

        error_text = str(exc_info.value).lower()
        assert error_text == expected_error
        for forbidden_fragment in (
            "c:\\",
            "users",
            "student",
            "token",
            "secret",
            "auth",
            "profile",
            "select",
            "sqlite",
            str(tmp_path).lower(),
            "traceback",
        ):
            assert forbidden_fragment not in error_text


def test_store_schema_is_limited_to_course_schedule_metadata(tmp_path: Path) -> None:
    db_path = tmp_path / "schedule.sqlite"
    save_course_schedule(db_path, _course_metadata(), _schedule_config())

    with sqlite3.connect(db_path) as connection:
        table_names = [
            row[0]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                ORDER BY name
                """
            ).fetchall()
        ]
        course_columns = [
            row[1] for row in connection.execute("PRAGMA table_info(courses)")
        ]
        class_time_columns = [
            row[1] for row in connection.execute("PRAGMA table_info(class_times)")
        ]

    assert table_names == ["class_times", "courses"]
    assert course_columns == [
        "course_id",
        "title",
        "instructor_name",
        "meeting_url",
        "meeting_label",
    ]
    assert class_time_columns == [
        "course_id",
        "position",
        "day_of_week",
        "local_start_time",
        "duration_minutes",
        "timezone_name",
        "meeting_label",
    ]
    schema_text = " ".join(table_names + course_columns + class_time_columns).lower()
    for forbidden_fragment in (
        "transcript",
        "event",
        "runtime",
        "artifact",
        "browser",
        "cookie",
        "audio",
        "media",
        "alert",
        "auth",
        "token",
        "secret",
    ):
        assert forbidden_fragment not in schema_text


def test_store_rejects_invalid_model_inputs(tmp_path: Path) -> None:
    db_path = tmp_path / "schedule.sqlite"

    with pytest.raises(ValueError) as save_exc:
        save_course_schedule(
            db_path,
            _course_metadata().model_copy(update={"meeting_url": "bad://private"}),
            _schedule_config(),
        )
    assert str(save_exc.value) == COURSE_SCHEDULE_SAVE_ERROR

    with pytest.raises(ValueError) as load_exc:
        load_course_schedule(db_path, "C:\\Users\\student\\token-secret-auth-profile")
    assert str(load_exc.value) == COURSE_SCHEDULE_LOAD_ERROR


def test_schedule_store_source_has_no_forbidden_execution_surfaces() -> None:
    source = Path(schedule_store.__file__).read_text(encoding="utf-8").lower()

    forbidden_tokens = [
        "requests",
        "httpx",
        "aiohttp",
        "playwright",
        "selenium",
        "webbrowser",
        "subprocess",
        "threading",
        "asyncio",
        "sounddevice",
        "faster_whisper",
        "telegram",
        "desktop_notifier",
        "datetime",
        "sleep",
        "timer",
        "open(",
        "read_text",
        "write_text",
        "copyfile",
        "rmtree",
    ]
    for forbidden_token in forbidden_tokens:
        assert forbidden_token not in source


def test_list_course_schedule_safe_summaries_source_stays_read_only() -> None:
    source = "\n".join(
        [
            inspect.getsource(schedule_store.list_course_schedule_safe_summaries),
            inspect.getsource(schedule_store._fetch_course_schedule_safe_summaries),
        ]
    ).lower()

    assert "mode=ro" in source
    assert "select" in source
    for forbidden_fragment in (
        "load_course_schedule(",
        "save_course_schedule",
        "initialize_course_schedule_store",
        "_create_schema",
        "create table",
        "insert into",
        "update ",
        "delete from",
        "drop table",
        "datetime",
        "now(",
        "sleep",
        "timer",
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
        "telegram",
        "desktop_notifier",
        "execute_archive",
        "archive_export",
        ".open(",
        ".read_text(",
        ".write_text(",
        ".mkdir(",
        ".unlink(",
        ".remove(",
        ".rmdir(",
        "rmtree",
    ):
        assert forbidden_fragment not in source


def test_list_course_schedule_due_list_inputs_source_stays_read_only_and_safe() -> None:
    source = "\n".join(
        [
            inspect.getsource(schedule_store.list_course_schedule_due_list_inputs),
            inspect.getsource(schedule_store._fetch_course_schedule_due_list_inputs),
        ]
    ).lower()

    assert "mode=ro" in source
    assert "select" in source
    for forbidden_fragment in (
        "title",
        "instructor_name",
        "meeting_url",
        "meeting_label",
        "timezone_name",
        "duration_minutes",
        "load_course_schedule(",
        "load_course_schedule_read_only",
        "load_course_schedule_safe_summary",
        "list_course_schedule_safe_summaries",
        "save_course_schedule",
        "initialize_course_schedule_store",
        "_create_schema",
        "create table",
        "insert into",
        "update ",
        "delete from",
        "drop table",
        "datetime",
        "now(",
        "sleep",
        "timer",
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
        "telegram",
        "desktop_notifier",
        "execute_archive",
        "archive_export",
        ".open(",
        ".read_text(",
        ".write_text(",
        ".mkdir(",
        ".unlink(",
        ".remove(",
        ".rmdir(",
        "rmtree",
    ):
        assert forbidden_fragment not in source
