"""Service for detecting interruptions in app usage patterns."""

from collections import defaultdict

from sense.models.events import AppUsageEvent, Interruption


class InterruptionService:
    """Detects interruptions where brief app switches break focus flow."""

    def calculate_interruptions(
        self, events: list[AppUsageEvent], max_interruption_seconds: float
    ) -> list[Interruption]:
        """Calculate interruptions from app usage events.

        An interruption occurs when:
        1. User is in App A
        2. Briefly switches to App B (duration <= max_interruption_seconds)
        3. Returns to App A

        Pattern: A → B (brief) → A

        Args:
            events: List of app usage events (must be sorted by start_time)
            max_interruption_seconds: Maximum duration for middle app to count as interruption

        Returns:
            List of interruptions sorted by time descending
        """
        if len(events) < 3:
            return []

        interruptions = []

        for i in range(len(events) - 2):
            prev_event = events[i]
            middle_event = events[i + 1]
            next_event = events[i + 2]

            # Check if pattern matches: A → B → A
            if prev_event.app_name == next_event.app_name and prev_event.app_name != middle_event.app_name:
                # Check if middle event is brief enough to be an interruption
                if middle_event.duration_seconds <= max_interruption_seconds:
                    gap_before = (middle_event.start_time - prev_event.end_time).total_seconds()
                    gap_after = (next_event.start_time - middle_event.end_time).total_seconds()

                    interruptions.append(
                        Interruption(
                            time=middle_event.start_time,
                            interrupted_app=prev_event.app_name,
                            interrupting_app=middle_event.app_name,
                            duration_seconds=middle_event.duration_seconds,
                            gap_before_seconds=gap_before,
                            gap_after_seconds=gap_after,
                        )
                    )

        # Sort by time descending (most recent first)
        return sorted(interruptions, key=lambda x: x.time, reverse=True)

    def filter_by_app(
        self, interruptions: list[Interruption], app_name: str, role: str = "both"
    ) -> list[Interruption]:
        """Filter interruptions involving a specific app.

        Args:
            interruptions: List of all interruptions
            app_name: App to filter by
            role: "interrupted", "interrupting", or "both"

        Returns:
            Filtered list of interruptions
        """
        if role == "interrupted":
            return [i for i in interruptions if i.interrupted_app == app_name]
        elif role == "interrupting":
            return [i for i in interruptions if i.interrupting_app == app_name]
        else:  # both
            return [
                i
                for i in interruptions
                if i.interrupted_app == app_name or i.interrupting_app == app_name
            ]

    def calculate_summary(
        self, interruptions: list[Interruption]
    ) -> dict[str, list[dict[str, float | int | str]]]:
        """Calculate summary statistics for interruptions.

        Args:
            interruptions: List of all interruptions

        Returns:
            Dict with "most_interrupting_apps" and "most_interrupted_apps" lists
        """
        # Track interrupting apps
        interrupting_counts: dict[str, int] = defaultdict(int)
        interrupting_durations: dict[str, list[float]] = defaultdict(list)

        for interruption in interruptions:
            interrupting_counts[interruption.interrupting_app] += 1
            interrupting_durations[interruption.interrupting_app].append(
                interruption.duration_seconds
            )

        # Track interrupted apps
        interrupted_counts: dict[str, int] = defaultdict(int)
        interrupted_durations: dict[str, list[float]] = defaultdict(list)

        for interruption in interruptions:
            interrupted_counts[interruption.interrupted_app] += 1
            interrupted_durations[interruption.interrupted_app].append(interruption.duration_seconds)

        # Build top interrupting apps
        most_interrupting: list[dict[str, float | int | str]] = []
        for app, count in sorted(interrupting_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            avg_duration = sum(interrupting_durations[app]) / len(interrupting_durations[app])
            most_interrupting.append(
                {"app_name": app, "count": count, "avg_duration_seconds": avg_duration}
            )

        # Build most interrupted apps
        most_interrupted: list[dict[str, float | int | str]] = []
        for app, count in sorted(interrupted_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            avg_duration = sum(interrupted_durations[app]) / len(interrupted_durations[app])
            most_interrupted.append(
                {"app_name": app, "count": count, "avg_duration_seconds": avg_duration}
            )

        return {"most_interrupting_apps": most_interrupting, "most_interrupted_apps": most_interrupted}
