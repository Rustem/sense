"""Service for calculating focus sessions from app usage events."""

from collections import defaultdict

from sense.models.events import AppUsageEvent, FocusSession


class FocusService:
    """Calculates focused work sessions grouped by app."""

    def calculate_focus_sessions(
        self, events: list[AppUsageEvent], gap_minutes: float
    ) -> dict[str, list[FocusSession]]:
        """Calculate focus sessions grouped by app.

        Args:
            events: List of app usage events (must be sorted by start_time)
            gap_minutes: Minutes of inactivity to split sessions

        Returns:
            Dict mapping app_name to list of focus sessions
        """
        if not events:
            return {}

        # Group events by app
        app_events = defaultdict(list)
        for event in events:
            app_events[event.app_name].append(event)

        # Calculate sessions for each app
        app_sessions = {}
        for app_name, app_event_list in app_events.items():
            # Sort by start time
            sorted_events = sorted(app_event_list, key=lambda e: e.start_time)
            sessions = self._detect_sessions(sorted_events, gap_minutes)
            app_sessions[app_name] = sessions

        return app_sessions

    def _detect_sessions(
        self, events: list[AppUsageEvent], gap_minutes: float
    ) -> list[FocusSession]:
        """Detect focus sessions from consecutive events of same app."""
        if not events:
            return []

        sessions = []
        current_session_events = [events[0]]

        for i in range(1, len(events)):
            gap = (events[i].start_time - events[i - 1].end_time).total_seconds() / 60

            if gap > gap_minutes:
                # Close current session
                sessions.append(self._create_session(current_session_events))
                current_session_events = [events[i]]
            else:
                current_session_events.append(events[i])

        # Close final session
        sessions.append(self._create_session(current_session_events))

        # Sort sessions by start time descending (most recent first)
        return sorted(sessions, key=lambda s: s.start, reverse=True)

    def _create_session(self, events: list[AppUsageEvent]) -> FocusSession:
        """Create a focus session from a list of consecutive events."""
        start = events[0].start_time
        end = events[-1].end_time
        duration_seconds = sum(e.duration_seconds for e in events)

        return FocusSession(
            app_name=events[0].app_name,
            start=start,
            end=end,
            duration_minutes=duration_seconds / 60,
            event_count=len(events),
        )

    def get_app_sessions(
        self, app_sessions: dict[str, list[FocusSession]], app_name: str
    ) -> list[FocusSession]:
        """Get sessions for a specific app."""
        return app_sessions.get(app_name, [])
