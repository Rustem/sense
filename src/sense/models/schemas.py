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
