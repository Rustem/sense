"""Service for calculating context switches from app usage events."""

from sense.models.events import AppUsageEvent, ContextSwitch


class ContextSwitchService:
    """Calculates context switches between apps."""

    def calculate_switches(
        self, events: list[AppUsageEvent], min_gap_seconds: float | None = None
    ) -> list[ContextSwitch]:
        """Calculate context switches from consecutive events.

        Args:
            events: List of app usage events (must be sorted by start_time)
            min_gap_seconds: Optional minimum gap to consider as a switch

        Returns:
            List of context switches
        """
        if len(events) < 2:
            return []

        switches = []
        for i in range(len(events) - 1):
            current = events[i]
            next_event = events[i + 1]

            gap = (next_event.start_time - current.end_time).total_seconds()

            # Apply minimum gap filter if specified
            if min_gap_seconds is not None and gap < min_gap_seconds:
                continue

            switches.append(
                ContextSwitch(
                    from_app=current.app_name,
                    to_app=next_event.app_name,
                    time=next_event.start_time,
                    gap_seconds=gap,
                )
            )

        return switches

    def filter_by_app(self, switches: list[ContextSwitch], app_name: str) -> list[ContextSwitch]:
        """Filter switches involving a specific app."""
        return [s for s in switches if s.from_app == app_name or s.to_app == app_name]
