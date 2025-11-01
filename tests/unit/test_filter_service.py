"""Tests for FilterService."""

from datetime import datetime

import pytest

from sense.core.filter_service import FilterService
from sense.models.events import AppUsageEvent


@pytest.fixture
def filter_service() -> FilterService:
    """Create FilterService instance."""
    return FilterService()


@pytest.fixture
def sample_event() -> AppUsageEvent:
    """Create sample app usage event."""
    return AppUsageEvent(
        app_name="IntelliJ IDEA",
        bundle_id="com.jetbrains.intellij",
        start_time=datetime(2024, 10, 31, 9, 0),
        end_time=datetime(2024, 10, 31, 9, 30),
        duration_seconds=1800.0,
    )


def test_should_exclude_global_blocked_domain(filter_service: FilterService) -> None:
    """Test global blocked domains are always excluded."""
    event = AppUsageEvent(
        app_name="pornhub.com",
        bundle_id="web",
        start_time=datetime.now(),
        end_time=datetime.now(),
        duration_seconds=100.0,
    )
    assert filter_service.should_exclude(event) is True


def test_should_exclude_system_app(filter_service: FilterService) -> None:
    """Test system apps excluded by default."""
    event = AppUsageEvent(
        app_name="QuickLook",
        bundle_id="com.apple.quicklook.QuickLookUIService",
        start_time=datetime.now(),
        end_time=datetime.now(),
        duration_seconds=10.0,
    )
    assert filter_service.should_exclude(event, include_system=False) is True
    assert filter_service.should_exclude(event, include_system=True) is False


def test_should_not_exclude_normal_app(
    filter_service: FilterService, sample_event: AppUsageEvent
) -> None:
    """Test normal apps are not excluded."""
    assert filter_service.should_exclude(sample_event) is False


def test_filter_events(filter_service: FilterService) -> None:
    """Test filtering list of events."""
    events = [
        AppUsageEvent(
            app_name="IntelliJ IDEA",
            bundle_id="com.jetbrains.intellij",
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration_seconds=1800.0,
        ),
        AppUsageEvent(
            app_name="pornhub.com",
            bundle_id="web",
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration_seconds=100.0,
        ),
        AppUsageEvent(
            app_name="QuickLook",
            bundle_id="com.apple.quicklook.QuickLookUIService",
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration_seconds=10.0,
        ),
    ]

    filtered = filter_service.filter_events(events, include_system=False)
    assert len(filtered) == 1
    assert filtered[0].app_name == "IntelliJ IDEA"

    filtered_with_system = filter_service.filter_events(events, include_system=True)
    assert len(filtered_with_system) == 2
