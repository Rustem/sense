"""Service for filtering app usage events."""

from sense.config import settings
from sense.models.events import AppUsageEvent


class FilterService:
    """Handles 3-level filtering: global, system, user."""

    def __init__(self) -> None:
        self.global_blocked = set(settings.global_blocked_domains)
        self.system_apps = set(settings.system_apps)
        self.user_excluded: set[str] = set()

    def should_exclude(self, event: AppUsageEvent, *, include_system: bool = False) -> bool:
        """Check if event should be excluded based on filters.

        Args:
            event: App usage event to check
            include_system: If True, don't filter system apps

        Returns:
            True if event should be excluded
        """
        # Level 1: Global blocked (always applied)
        if event.app_name in self.global_blocked or event.bundle_id in self.global_blocked:
            return True

        # Level 2: System apps (optional)
        if not include_system:
            if event.bundle_id in self.system_apps:
                return True

        # Level 3: User custom exclusions (future)
        if event.app_name in self.user_excluded or event.bundle_id in self.user_excluded:
            return True

        return False

    def filter_events(
        self, events: list[AppUsageEvent], *, include_system: bool = False
    ) -> list[AppUsageEvent]:
        """Filter list of events based on exclusion rules."""
        return [e for e in events if not self.should_exclude(e, include_system=include_system)]
