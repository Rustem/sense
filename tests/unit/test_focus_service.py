"""Unit tests for FocusService."""

from datetime import datetime

import pytest

from sense.core.focus_service import FocusService
from sense.models.events import AppUsageEvent


@pytest.fixture
def service():
    return FocusService()


@pytest.fixture
def sample_events():
    """Create sample events for testing."""
    return [
        # IntelliJ session 1
        AppUsageEvent(
            app_name="IntelliJ",
            bundle_id="com.jetbrains.intellij",
            start_time=datetime(2025, 10, 14, 9, 0, 0),
            end_time=datetime(2025, 10, 14, 9, 15, 0),
            duration_seconds=900,
        ),
        AppUsageEvent(
            app_name="IntelliJ",
            bundle_id="com.jetbrains.intellij",
            start_time=datetime(2025, 10, 14, 9, 16, 0),  # 1 min gap
            end_time=datetime(2025, 10, 14, 9, 30, 0),
            duration_seconds=840,
        ),
        # 10 min gap - new session
        # IntelliJ session 2
        AppUsageEvent(
            app_name="IntelliJ",
            bundle_id="com.jetbrains.intellij",
            start_time=datetime(2025, 10, 14, 9, 40, 0),
            end_time=datetime(2025, 10, 14, 10, 0, 0),
            duration_seconds=1200,
        ),
        # Safari session
        AppUsageEvent(
            app_name="Safari",
            bundle_id="com.apple.Safari",
            start_time=datetime(2025, 10, 14, 10, 5, 0),
            end_time=datetime(2025, 10, 14, 10, 15, 0),
            duration_seconds=600,
        ),
    ]


def test_calculate_focus_sessions_basic(service, sample_events):
    """Test basic focus session calculation."""
    app_sessions = service.calculate_focus_sessions(sample_events, gap_minutes=5.0)

    assert len(app_sessions) == 2
    assert "IntelliJ" in app_sessions
    assert "Safari" in app_sessions

    intellij_sessions = app_sessions["IntelliJ"]
    assert len(intellij_sessions) == 2

    # Sessions are sorted DESC by start time
    assert intellij_sessions[0].start == datetime(2025, 10, 14, 9, 40, 0)
    assert intellij_sessions[0].duration_minutes == 20.0
    assert intellij_sessions[0].event_count == 1

    assert intellij_sessions[1].start == datetime(2025, 10, 14, 9, 0, 0)
    assert intellij_sessions[1].end == datetime(2025, 10, 14, 9, 30, 0)
    assert intellij_sessions[1].duration_minutes == 29.0
    assert intellij_sessions[1].event_count == 2


def test_calculate_focus_sessions_empty(service):
    """Test with empty event list."""
    app_sessions = service.calculate_focus_sessions([], gap_minutes=5.0)
    assert app_sessions == {}


def test_calculate_focus_sessions_single_event(service):
    """Test with single event."""
    events = [
        AppUsageEvent(
            app_name="App1",
            bundle_id="com.app1",
            start_time=datetime(2025, 10, 14, 10, 0, 0),
            end_time=datetime(2025, 10, 14, 10, 5, 0),
            duration_seconds=300,
        )
    ]

    app_sessions = service.calculate_focus_sessions(events, gap_minutes=5.0)
    assert len(app_sessions) == 1
    assert len(app_sessions["App1"]) == 1
    assert app_sessions["App1"][0].duration_minutes == 5.0


def test_detect_sessions_no_gaps(service):
    """Test session detection with continuous events (no gaps)."""
    events = [
        AppUsageEvent(
            app_name="App1",
            bundle_id="com.app1",
            start_time=datetime(2025, 10, 14, 10, 0, 0),
            end_time=datetime(2025, 10, 14, 10, 5, 0),
            duration_seconds=300,
        ),
        AppUsageEvent(
            app_name="App1",
            bundle_id="com.app1",
            start_time=datetime(2025, 10, 14, 10, 5, 0),
            end_time=datetime(2025, 10, 14, 10, 10, 0),
            duration_seconds=300,
        ),
    ]

    sessions = service._detect_sessions(events, gap_minutes=5.0)
    assert len(sessions) == 1
    assert sessions[0].duration_minutes == 10.0
    assert sessions[0].event_count == 2


def test_detect_sessions_with_gap_above_threshold(service):
    """Test session detection with gap above threshold."""
    events = [
        AppUsageEvent(
            app_name="App1",
            bundle_id="com.app1",
            start_time=datetime(2025, 10, 14, 10, 0, 0),
            end_time=datetime(2025, 10, 14, 10, 5, 0),
            duration_seconds=300,
        ),
        AppUsageEvent(
            app_name="App1",
            bundle_id="com.app1",
            start_time=datetime(2025, 10, 14, 10, 11, 0),  # 6 min gap
            end_time=datetime(2025, 10, 14, 10, 15, 0),
            duration_seconds=240,
        ),
    ]

    sessions = service._detect_sessions(events, gap_minutes=5.0)
    assert len(sessions) == 2
    assert sessions[0].duration_minutes == 4.0  # DESC order
    assert sessions[1].duration_minutes == 5.0


def test_detect_sessions_with_gap_below_threshold(service):
    """Test session detection with gap below threshold."""
    events = [
        AppUsageEvent(
            app_name="App1",
            bundle_id="com.app1",
            start_time=datetime(2025, 10, 14, 10, 0, 0),
            end_time=datetime(2025, 10, 14, 10, 5, 0),
            duration_seconds=300,
        ),
        AppUsageEvent(
            app_name="App1",
            bundle_id="com.app1",
            start_time=datetime(2025, 10, 14, 10, 8, 0),  # 3 min gap
            end_time=datetime(2025, 10, 14, 10, 15, 0),
            duration_seconds=420,
        ),
    ]

    sessions = service._detect_sessions(events, gap_minutes=5.0)
    assert len(sessions) == 1
    assert sessions[0].duration_minutes == 12.0
    assert sessions[0].event_count == 2


def test_get_app_sessions(service, sample_events):
    """Test getting sessions for specific app."""
    app_sessions = service.calculate_focus_sessions(sample_events, gap_minutes=5.0)

    intellij_sessions = service.get_app_sessions(app_sessions, "IntelliJ")
    assert len(intellij_sessions) == 2

    safari_sessions = service.get_app_sessions(app_sessions, "Safari")
    assert len(safari_sessions) == 1

    nonexistent = service.get_app_sessions(app_sessions, "com.nonexistent")
    assert nonexistent == []


def test_session_sorting_desc(service):
    """Test that sessions are sorted by start time descending."""
    events = [
        AppUsageEvent(
            app_name="App1",
            bundle_id="com.app1",
            start_time=datetime(2025, 10, 14, 9, 0, 0),
            end_time=datetime(2025, 10, 14, 9, 5, 0),
            duration_seconds=300,
        ),
        AppUsageEvent(
            app_name="App1",
            bundle_id="com.app1",
            start_time=datetime(2025, 10, 14, 11, 0, 0),  # 2 hours later
            end_time=datetime(2025, 10, 14, 11, 5, 0),
            duration_seconds=300,
        ),
    ]

    sessions = service._detect_sessions(events, gap_minutes=5.0)
    assert len(sessions) == 2
    assert sessions[0].start > sessions[1].start  # DESC order


def test_create_session(service):
    """Test session creation from events."""
    events = [
        AppUsageEvent(
            app_name="App1",
            bundle_id="com.app1",
            start_time=datetime(2025, 10, 14, 10, 0, 0),
            end_time=datetime(2025, 10, 14, 10, 5, 0),
            duration_seconds=300,
        ),
        AppUsageEvent(
            app_name="App1",
            bundle_id="com.app1",
            start_time=datetime(2025, 10, 14, 10, 5, 0),
            end_time=datetime(2025, 10, 14, 10, 10, 0),
            duration_seconds=300,
        ),
    ]

    session = service._create_session(events)
    assert session.app_name == "App1"
    assert session.start == datetime(2025, 10, 14, 10, 0, 0)
    assert session.end == datetime(2025, 10, 14, 10, 10, 0)
    assert session.duration_minutes == 10.0
    assert session.event_count == 2
