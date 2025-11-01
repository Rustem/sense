"""Unit tests for ContextSwitchService."""

from datetime import datetime

import pytest

from sense.core.context_switch_service import ContextSwitchService
from sense.models.events import AppUsageEvent


@pytest.fixture
def service():
    return ContextSwitchService()


@pytest.fixture
def sample_events():
    """Create sample events for testing."""
    return [
        AppUsageEvent(
            app_name="Mail",
            bundle_id="com.apple.mail",
            start_time=datetime(2025, 10, 14, 19, 0, 0),
            end_time=datetime(2025, 10, 14, 19, 6, 20),
            duration_seconds=380,
        ),
        AppUsageEvent(
            app_name="Safari",
            bundle_id="com.apple.Safari",
            start_time=datetime(2025, 10, 14, 19, 6, 34),
            end_time=datetime(2025, 10, 14, 19, 15, 0),
            duration_seconds=506,
        ),
        AppUsageEvent(
            app_name="Slack",
            bundle_id="com.tinyspeck.slackmacgap",
            start_time=datetime(2025, 10, 14, 19, 15, 2),
            end_time=datetime(2025, 10, 14, 19, 20, 0),
            duration_seconds=298,
        ),
    ]


def test_calculate_switches_basic(service, sample_events):
    """Test basic switch calculation."""
    switches = service.calculate_switches(sample_events)

    assert len(switches) == 2
    assert switches[0].from_app == "com.apple.mail"
    assert switches[0].to_app == "com.apple.Safari"
    assert switches[0].time == datetime(2025, 10, 14, 19, 6, 34)
    assert switches[0].gap_seconds == 14.0

    assert switches[1].from_app == "com.apple.Safari"
    assert switches[1].to_app == "com.tinyspeck.slackmacgap"
    assert switches[1].time == datetime(2025, 10, 14, 19, 15, 2)
    assert switches[1].gap_seconds == 2.0


def test_calculate_switches_empty_list(service):
    """Test with empty event list."""
    switches = service.calculate_switches([])
    assert switches == []


def test_calculate_switches_single_event(service, sample_events):
    """Test with single event."""
    switches = service.calculate_switches([sample_events[0]])
    assert switches == []


def test_calculate_switches_with_min_gap(service, sample_events):
    """Test filtering switches by minimum gap."""
    switches = service.calculate_switches(sample_events, min_gap_seconds=5.0)

    assert len(switches) == 1
    assert switches[0].from_app == "com.apple.mail"
    assert switches[0].to_app == "com.apple.Safari"
    assert switches[0].gap_seconds == 14.0


def test_calculate_switches_negative_gap(service):
    """Test with overlapping events (negative gap)."""
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
            start_time=datetime(2025, 10, 14, 10, 3, 0),  # Starts before first ends
            end_time=datetime(2025, 10, 14, 10, 8, 0),
            duration_seconds=300,
        ),
    ]

    switches = service.calculate_switches(events)
    assert len(switches) == 1
    assert switches[0].gap_seconds == -120.0  # 2 minutes overlap


def test_calculate_switches_zero_gap(service):
    """Test with consecutive events (zero gap)."""
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
            end_time=datetime(2025, 10, 14, 10, 8, 0),
            duration_seconds=180,
        ),
    ]

    switches = service.calculate_switches(events)
    assert len(switches) == 1
    assert switches[0].gap_seconds == 0.0


def test_filter_by_app(service, sample_events):
    """Test filtering switches by app."""
    all_switches = service.calculate_switches(sample_events)

    # Filter by Safari
    safari_switches = service.filter_by_app(all_switches, "com.apple.Safari")
    assert len(safari_switches) == 2
    assert all(
        s.from_app == "com.apple.Safari" or s.to_app == "com.apple.Safari"
        for s in safari_switches
    )

    # Filter by Mail
    mail_switches = service.filter_by_app(all_switches, "com.apple.mail")
    assert len(mail_switches) == 1
    assert mail_switches[0].from_app == "com.apple.mail"

    # Filter by non-existent app
    none_switches = service.filter_by_app(all_switches, "com.nonexistent")
    assert len(none_switches) == 0
