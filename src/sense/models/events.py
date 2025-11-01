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
