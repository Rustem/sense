"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class EventSchema(BaseModel):
    """Single event in timeline response."""

    app_name: str
    bundle_id: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float


class TimelineResponse(BaseModel):
    """Response for timeline endpoints."""

    start_date: str
    end_date: str
    page: int
    limit: int
    total_events: int
    total_pages: int
    events: list[EventSchema]


class TimelineQuery(BaseModel):
    """Query parameters for timeline endpoints."""

    start_date: str
    end_date: str | None = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=100, ge=1, le=1000)
    order: Literal["asc", "desc"] = "desc"
    include_system: bool = False


class ContextSwitchSchema(BaseModel):
    """Single context switch in switches response."""

    from_app: str
    to_app: str
    time: datetime
    gap_seconds: float


class SwitchesResponse(BaseModel):
    """Response for context switches endpoints."""

    start_date: str
    end_date: str
    page: int
    limit: int
    total_switches: int
    total_pages: int
    switches: list[ContextSwitchSchema]


class FocusSessionSchema(BaseModel):
    """Single focus session in focus response."""

    start: datetime
    end: datetime
    duration_minutes: float


class AppFocusSchema(BaseModel):
    """Focus metrics for a single app."""

    app_name: str
    total_time_minutes: float
    total_sessions: int
    avg_session_minutes: float
    longest_session_minutes: float
    focus_sessions: list[FocusSessionSchema]


class FocusResponse(BaseModel):
    """Response for focus endpoints (all apps)."""

    start_date: str
    end_date: str
    page: int
    limit: int
    total_apps: int
    total_pages: int
    apps: list[AppFocusSchema]


class AppFocusDetailResponse(BaseModel):
    """Response for single app focus endpoint."""

    app_name: str
    start_date: str
    end_date: str
    total_time_minutes: float
    total_sessions: int
    avg_session_minutes: float
    longest_session_minutes: float
    shortest_session_minutes: float
    focus_sessions: list[FocusSessionSchema]


class InterruptionSchema(BaseModel):
    """Single interruption in interruptions response."""

    time: datetime
    interrupted_app: str
    interrupting_app: str
    duration_seconds: float
    gap_before_seconds: float
    gap_after_seconds: float


class AppInterruptionSummary(BaseModel):
    """Summary of interruptions for a single app."""

    app_name: str
    count: int
    avg_duration_seconds: float


class InterruptionsResponse(BaseModel):
    """Response for interruptions endpoints."""

    start_date: str
    end_date: str
    max_interruption_seconds: int
    page: int
    limit: int
    total_interruptions: int
    total_pages: int
    interruptions: list[InterruptionSchema]
    summary: dict[str, list[AppInterruptionSummary]]


class AppInterruptionsResponse(BaseModel):
    """Response for single app interruptions endpoint."""

    app_name: str
    start_date: str
    end_date: str
    max_interruption_seconds: int
    role: str
    total_interruptions: int
    avg_duration_seconds: float
    interruptions: list[InterruptionSchema]
