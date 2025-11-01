"""Tests for KnowledgeCRepository."""

import sqlite3
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from sense.core.knowledgec_repository import KnowledgeCRepository


@pytest.fixture
def temp_db() -> Path:
    """Create temporary test database with sample data."""
    temp_file = NamedTemporaryFile(delete=False, suffix=".db")
    db_path = Path(temp_file.name)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute(
        """
        CREATE TABLE ZOBJECT (
            Z_PK INTEGER PRIMARY KEY,
            ZSTREAMNAME TEXT,
            ZSTARTDATE REAL,
            ZENDDATE REAL,
            ZVALUESTRING TEXT,
            ZSOURCE INTEGER,
            ZSTRUCTUREDMETADATA INTEGER
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE ZSOURCE (
            Z_PK INTEGER PRIMARY KEY,
            ZBUNDLEID TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE ZSTRUCTUREDMETADATA (
            Z_PK INTEGER PRIMARY KEY,
            Z_DKDIGITALHEALTHMETADATAKEY__WEBDOMAIN TEXT
        )
        """
    )

    # macOS epoch offset
    OFFSET = 978307200

    # Insert test data for 2024-10-31
    test_date = datetime(2024, 10, 31, 10, 0, 0)
    start_ts = test_date.timestamp() - OFFSET

    # Event 1: 10:00 - 10:30 (1800 seconds)
    cursor.execute(
        """
        INSERT INTO ZOBJECT (Z_PK, ZSTREAMNAME, ZSTARTDATE, ZENDDATE, ZVALUESTRING, ZSOURCE)
        VALUES (1, '/app/usage', ?, ?, 'TestApp', 1)
        """,
        (start_ts, start_ts + 1800),
    )

    cursor.execute(
        """
        INSERT INTO ZSOURCE (Z_PK, ZBUNDLEID)
        VALUES (1, 'com.test.app')
        """
    )

    # Event 2: 11:00 - 11:15 (900 seconds)
    cursor.execute(
        """
        INSERT INTO ZOBJECT (Z_PK, ZSTREAMNAME, ZSTARTDATE, ZENDDATE, ZVALUESTRING, ZSOURCE)
        VALUES (2, '/app/usage', ?, ?, 'AnotherApp', 2)
        """,
        (start_ts + 3600, start_ts + 3600 + 900),
    )

    cursor.execute(
        """
        INSERT INTO ZSOURCE (Z_PK, ZBUNDLEID)
        VALUES (2, 'com.another.app')
        """
    )

    # Event 3: Next day (2024-11-01)
    next_day = datetime(2024, 11, 1, 10, 0, 0)
    next_day_ts = next_day.timestamp() - OFFSET

    cursor.execute(
        """
        INSERT INTO ZOBJECT (Z_PK, ZSTREAMNAME, ZSTARTDATE, ZENDDATE, ZVALUESTRING, ZSOURCE)
        VALUES (3, '/app/usage', ?, ?, 'TestApp', 1)
        """,
        (next_day_ts, next_day_ts + 600),
    )

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    db_path.unlink()


def test_repository_init_file_not_found() -> None:
    """Test repository raises error if database doesn't exist."""
    with pytest.raises(FileNotFoundError):
        KnowledgeCRepository(Path("/nonexistent/path.db"))


def test_get_events_single_day(temp_db: Path) -> None:
    """Test querying events for a single day."""
    repo = KnowledgeCRepository(temp_db)

    # Both start and end should be start of day (00:00:00)
    start = datetime(2024, 10, 31, 0, 0, 0)
    end = datetime(2024, 10, 31, 0, 0, 0)

    events = repo.get_events(start, end)

    assert len(events) == 2
    assert events[0].app_name == "TestApp"
    assert events[0].duration_seconds == 1800.0
    assert events[1].app_name == "AnotherApp"
    assert events[1].duration_seconds == 900.0


def test_get_events_excludes_next_day(temp_db: Path) -> None:
    """Test that single day query excludes events from next day."""
    repo = KnowledgeCRepository(temp_db)

    start = datetime(2024, 10, 31, 0, 0, 0)
    end = datetime(2024, 10, 31, 0, 0, 0)

    events = repo.get_events(start, end)

    # Should only get 2 events from Oct 31, not the Nov 1 event
    assert len(events) == 2
    assert all(e.start_time.day == 31 for e in events)


def test_get_events_multi_day(temp_db: Path) -> None:
    """Test querying events across multiple days."""
    repo = KnowledgeCRepository(temp_db)

    start = datetime(2024, 10, 31, 0, 0, 0)
    end = datetime(2024, 11, 1, 0, 0, 0)

    events = repo.get_events(start, end)

    # Should get all 3 events
    assert len(events) == 3


def test_get_events_with_app_filter(temp_db: Path) -> None:
    """Test filtering events by app name."""
    repo = KnowledgeCRepository(temp_db)

    start = datetime(2024, 10, 31, 0, 0, 0)
    end = datetime(2024, 10, 31, 0, 0, 0)

    events = repo.get_events(start, end, app_name="TestApp")

    assert len(events) == 1
    assert events[0].app_name == "TestApp"


def test_get_events_sorted_by_start_time(temp_db: Path) -> None:
    """Test events are sorted by start time."""
    repo = KnowledgeCRepository(temp_db)

    start = datetime(2024, 10, 31, 0, 0, 0)
    end = datetime(2024, 11, 1, 0, 0, 0)

    events = repo.get_events(start, end)

    # Verify chronological order
    for i in range(len(events) - 1):
        assert events[i].start_time <= events[i + 1].start_time
