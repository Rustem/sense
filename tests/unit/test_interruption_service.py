"""Unit tests for InterruptionService."""

from datetime import datetime

import pytest

from sense.core.interruption_service import InterruptionService
from sense.models.events import AppUsageEvent


@pytest.fixture
def service():
    return InterruptionService()


@pytest.fixture
def sample_events():
    """Create sample events for testing interruptions."""
    return [
        # IntelliJ work
        AppUsageEvent(
            app_name="IntelliJ",
            bundle_id="com.jetbrains.intellij",
            start_time=datetime(2025, 10, 14, 9, 0, 0),
            end_time=datetime(2025, 10, 14, 9, 15, 0),
            duration_seconds=900,
        ),
        # Slack interruption (1 min)
        AppUsageEvent(
            app_name="Slack",
            bundle_id="com.tinyspeck.slackmacgap",
            start_time=datetime(2025, 10, 14, 9, 15, 0),
            end_time=datetime(2025, 10, 14, 9, 16, 0),
            duration_seconds=60,
        ),
        # Resume IntelliJ
        AppUsageEvent(
            app_name="IntelliJ",
            bundle_id="com.jetbrains.intellij",
            start_time=datetime(2025, 10, 14, 9, 16, 0),
            end_time=datetime(2025, 10, 14, 9, 30, 0),
            duration_seconds=840,
        ),
        # Mail interruption (30 sec)
        AppUsageEvent(
            app_name="Mail",
            bundle_id="com.apple.mail",
            start_time=datetime(2025, 10, 14, 9, 30, 0),
            end_time=datetime(2025, 10, 14, 9, 30, 30),
            duration_seconds=30,
        ),
        # Resume IntelliJ again
        AppUsageEvent(
            app_name="IntelliJ",
            bundle_id="com.jetbrains.intellij",
            start_time=datetime(2025, 10, 14, 9, 30, 30),
            end_time=datetime(2025, 10, 14, 10, 0, 0),
            duration_seconds=1770,
        ),
    ]


def test_calculate_interruptions_basic(service, sample_events):
    """Test basic interruption detection."""
    interruptions = service.calculate_interruptions(sample_events, max_interruption_seconds=300)

    assert len(interruptions) == 2

    # Most recent first (DESC order)
    assert interruptions[0].interrupting_app == "Mail"
    assert interruptions[0].interrupted_app == "IntelliJ"
    assert interruptions[0].duration_seconds == 30
    assert interruptions[0].gap_before_seconds == 0
    assert interruptions[0].gap_after_seconds == 0

    assert interruptions[1].interrupting_app == "Slack"
    assert interruptions[1].interrupted_app == "IntelliJ"
    assert interruptions[1].duration_seconds == 60


def test_calculate_interruptions_empty_list(service):
    """Test with empty event list."""
    interruptions = service.calculate_interruptions([], max_interruption_seconds=300)
    assert interruptions == []


def test_calculate_interruptions_too_few_events(service):
    """Test with less than 3 events."""
    events = [
        AppUsageEvent(
            app_name="App1",
            bundle_id="com.app1",
            start_time=datetime(2025, 10, 14, 10, 0, 0),
            end_time=datetime(2025, 10, 14, 10, 5, 0),
            duration_seconds=300,
        ),
        AppUsageEvent(
            app_name="App2",
            bundle_id="com.app2",
            start_time=datetime(2025, 10, 14, 10, 5, 0),
            end_time=datetime(2025, 10, 14, 10, 6, 0),
            duration_seconds=60,
        ),
    ]

    interruptions = service.calculate_interruptions(events, max_interruption_seconds=300)
    assert interruptions == []


def test_interruption_too_long_ignored(service):
    """Test that long middle events are not counted as interruptions."""
    events = [
        AppUsageEvent(
            app_name="App1",
            bundle_id="com.app1",
            start_time=datetime(2025, 10, 14, 9, 0, 0),
            end_time=datetime(2025, 10, 14, 9, 15, 0),
            duration_seconds=900,
        ),
        # 10 minute interruption - too long
        AppUsageEvent(
            app_name="App2",
            bundle_id="com.app2",
            start_time=datetime(2025, 10, 14, 9, 15, 0),
            end_time=datetime(2025, 10, 14, 9, 25, 0),
            duration_seconds=600,
        ),
        AppUsageEvent(
            app_name="App1",
            bundle_id="com.app1",
            start_time=datetime(2025, 10, 14, 9, 25, 0),
            end_time=datetime(2025, 10, 14, 9, 40, 0),
            duration_seconds=900,
        ),
    ]

    interruptions = service.calculate_interruptions(events, max_interruption_seconds=300)
    assert len(interruptions) == 0


def test_no_return_to_original_app(service):
    """Test that A→B→C pattern is not an interruption."""
    events = [
        AppUsageEvent(
            app_name="App1",
            bundle_id="com.app1",
            start_time=datetime(2025, 10, 14, 9, 0, 0),
            end_time=datetime(2025, 10, 14, 9, 15, 0),
            duration_seconds=900,
        ),
        AppUsageEvent(
            app_name="App2",
            bundle_id="com.app2",
            start_time=datetime(2025, 10, 14, 9, 15, 0),
            end_time=datetime(2025, 10, 14, 9, 16, 0),
            duration_seconds=60,
        ),
        # Different app (App3, not App1)
        AppUsageEvent(
            app_name="App3",
            bundle_id="com.app3",
            start_time=datetime(2025, 10, 14, 9, 16, 0),
            end_time=datetime(2025, 10, 14, 9, 30, 0),
            duration_seconds=840,
        ),
    ]

    interruptions = service.calculate_interruptions(events, max_interruption_seconds=300)
    assert len(interruptions) == 0


def test_interruption_with_gaps(service):
    """Test interruption detection with gaps before/after."""
    events = [
        AppUsageEvent(
            app_name="App1",
            bundle_id="com.app1",
            start_time=datetime(2025, 10, 14, 9, 0, 0),
            end_time=datetime(2025, 10, 14, 9, 15, 0),
            duration_seconds=900,
        ),
        # 2 min gap before interruption
        AppUsageEvent(
            app_name="App2",
            bundle_id="com.app2",
            start_time=datetime(2025, 10, 14, 9, 17, 0),
            end_time=datetime(2025, 10, 14, 9, 18, 0),
            duration_seconds=60,
        ),
        # 1 min gap after interruption
        AppUsageEvent(
            app_name="App1",
            bundle_id="com.app1",
            start_time=datetime(2025, 10, 14, 9, 19, 0),
            end_time=datetime(2025, 10, 14, 9, 30, 0),
            duration_seconds=660,
        ),
    ]

    interruptions = service.calculate_interruptions(events, max_interruption_seconds=300)
    assert len(interruptions) == 1
    assert interruptions[0].gap_before_seconds == 120
    assert interruptions[0].gap_after_seconds == 60


def test_multiple_interruptions_same_pair(service):
    """Test multiple interruptions between same app pair."""
    events = [
        AppUsageEvent(
            app_name="App1",
            bundle_id="com.app1",
            start_time=datetime(2025, 10, 14, 9, 0, 0),
            end_time=datetime(2025, 10, 14, 9, 10, 0),
            duration_seconds=600,
        ),
        AppUsageEvent(
            app_name="App2",
            bundle_id="com.app2",
            start_time=datetime(2025, 10, 14, 9, 10, 0),
            end_time=datetime(2025, 10, 14, 9, 11, 0),
            duration_seconds=60,
        ),
        AppUsageEvent(
            app_name="App1",
            bundle_id="com.app1",
            start_time=datetime(2025, 10, 14, 9, 11, 0),
            end_time=datetime(2025, 10, 14, 9, 20, 0),
            duration_seconds=540,
        ),
        AppUsageEvent(
            app_name="App2",
            bundle_id="com.app2",
            start_time=datetime(2025, 10, 14, 9, 20, 0),
            end_time=datetime(2025, 10, 14, 9, 21, 0),
            duration_seconds=60,
        ),
        AppUsageEvent(
            app_name="App1",
            bundle_id="com.app1",
            start_time=datetime(2025, 10, 14, 9, 21, 0),
            end_time=datetime(2025, 10, 14, 9, 30, 0),
            duration_seconds=540,
        ),
    ]

    interruptions = service.calculate_interruptions(events, max_interruption_seconds=300)
    assert len(interruptions) == 2
    assert all(i.interrupting_app == "App2" for i in interruptions)
    assert all(i.interrupted_app == "App1" for i in interruptions)


def test_filter_by_app_interrupted(service, sample_events):
    """Test filtering interruptions by interrupted app."""
    all_interruptions = service.calculate_interruptions(sample_events, max_interruption_seconds=300)

    intellij_interrupted = service.filter_by_app(
        all_interruptions, "IntelliJ", role="interrupted"
    )
    assert len(intellij_interrupted) == 2
    assert all(i.interrupted_app == "IntelliJ" for i in intellij_interrupted)


def test_filter_by_app_interrupting(service, sample_events):
    """Test filtering interruptions by interrupting app."""
    all_interruptions = service.calculate_interruptions(sample_events, max_interruption_seconds=300)

    slack_interrupting = service.filter_by_app(
        all_interruptions, "Slack", role="interrupting"
    )
    assert len(slack_interrupting) == 1
    assert slack_interrupting[0].interrupting_app == "Slack"


def test_filter_by_app_both(service, sample_events):
    """Test filtering interruptions by app (both roles)."""
    all_interruptions = service.calculate_interruptions(sample_events, max_interruption_seconds=300)

    intellij_both = service.filter_by_app(
        all_interruptions, "IntelliJ", role="both"
    )
    assert len(intellij_both) == 2


def test_calculate_summary(service, sample_events):
    """Test summary calculation."""
    interruptions = service.calculate_interruptions(sample_events, max_interruption_seconds=300)
    summary = service.calculate_summary(interruptions)

    assert "most_interrupting_apps" in summary
    assert "most_interrupted_apps" in summary

    # Check most interrupting apps
    assert len(summary["most_interrupting_apps"]) == 2
    assert summary["most_interrupting_apps"][0]["app_name"] in [
        "Slack",
        "Mail",
    ]
    assert summary["most_interrupting_apps"][0]["count"] == 1

    # Check most interrupted apps
    assert len(summary["most_interrupted_apps"]) == 1
    assert summary["most_interrupted_apps"][0]["app_name"] == "IntelliJ"
    assert summary["most_interrupted_apps"][0]["count"] == 2


def test_interruptions_sorted_desc(service, sample_events):
    """Test that interruptions are sorted by time descending."""
    interruptions = service.calculate_interruptions(sample_events, max_interruption_seconds=300)

    assert len(interruptions) == 2
    # Most recent first
    assert interruptions[0].time > interruptions[1].time
