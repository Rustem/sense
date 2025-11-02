"""Event models for KnowledgeC database."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class AppUsageEvent:
    """Single app usage event from KnowledgeC."""

    app_name: str
    bundle_id: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float

    @property
    def duration_minutes(self) -> float:
        return self.duration_seconds / 60

    @property
    def date(self) -> str:
        return self.start_time.strftime("%Y-%m-%d")


@dataclass
class ContextSwitch:
    """Context switch between two apps."""

    from_app: str
    to_app: str
    time: datetime
    gap_seconds: float


@dataclass
class FocusSession:
    """Focused work session for a single app."""

    app_name: str
    start: datetime
    end: datetime
    duration_minutes: float
    event_count: int


@dataclass
class Interruption:
    """An interruption event where brief app switch breaks focus flow."""

    time: datetime
    interrupted_app: str
    interrupting_app: str
    duration_seconds: float
    gap_before_seconds: float
    gap_after_seconds: float
