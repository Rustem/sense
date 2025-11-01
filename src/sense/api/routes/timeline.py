"""Timeline API routes."""

import math
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from sense.config import settings
from sense.core.cache import InMemoryCache
from sense.core.filter_service import FilterService
from sense.core.knowledgec_repository import KnowledgeCRepository
from sense.models.schemas import EventSchema, TimelineResponse

router = APIRouter(prefix="/timeline", tags=["timeline"])

# Initialize services
repository = KnowledgeCRepository(settings.knowledgec_db_path)
filter_service = FilterService()
cache = InMemoryCache(ttl_seconds=settings.cache_ttl_seconds)


def parse_date(date_str: str) -> datetime:
    """Parse YYYY-MM-DD date string to datetime."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {date_str}") from e


def validate_date_range(start: datetime, end: datetime) -> None:
    """Validate date range is within limits."""
    if end < start:
        raise HTTPException(status_code=400, detail="end_date must be >= start_date")

    delta = (end - start).days
    if delta > settings.max_date_range_days:
        raise HTTPException(
            status_code=400,
            detail=f"Date range cannot exceed {settings.max_date_range_days} days",
        )


@router.get("", response_model=TimelineResponse)
def get_timeline(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="End date (YYYY-MM-DD), defaults to now"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(100, ge=1, le=1000, description="Events per page"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    include_system: bool = Query(False, description="Include system apps"),
) -> TimelineResponse:
    """Get timeline of all app usage events."""
    start = parse_date(start_date)
    end = parse_date(end_date) if end_date else datetime.now()
    validate_date_range(start, end)

    # Generate cache key
    cache_key = f"timeline:{start_date}:{end_date}:{include_system}"
    cached = cache.get(cache_key)
    if cached:
        events = cached
    else:
        # Query database
        events = repository.get_events(start, end)
        # Apply filters
        events = filter_service.filter_events(events, include_system=include_system)
        cache.set(cache_key, events)

    # Sort
    if order == "desc":
        events = sorted(events, key=lambda e: e.start_time, reverse=True)

    # Paginate
    total_events = len(events)
    total_pages = math.ceil(total_events / limit)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    page_events = events[start_idx:end_idx]

    return TimelineResponse(
        start_date=start_date,
        end_date=end_date or datetime.now().strftime("%Y-%m-%d"),
        page=page,
        limit=limit,
        total_events=total_events,
        total_pages=total_pages,
        events=[
            EventSchema(
                app_name=e.app_name,
                bundle_id=e.bundle_id,
                start_time=e.start_time,
                end_time=e.end_time,
                duration_seconds=e.duration_seconds,
            )
            for e in page_events
        ],
    )


@router.get("/{app_name}", response_model=TimelineResponse)
def get_app_timeline(
    app_name: str,
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="End date (YYYY-MM-DD), defaults to now"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(100, ge=1, le=1000, description="Events per page"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    include_system: bool = Query(False, description="Include system apps"),
) -> TimelineResponse:
    """Get timeline for specific app."""
    start = parse_date(start_date)
    end = parse_date(end_date) if end_date else datetime.now()
    validate_date_range(start, end)

    # Generate cache key
    cache_key = f"timeline:{app_name}:{start_date}:{end_date}:{include_system}"
    cached = cache.get(cache_key)
    if cached:
        events = cached
    else:
        # Query database with app filter
        events = repository.get_events(start, end, app_name=app_name)
        # Apply filters
        events = filter_service.filter_events(events, include_system=include_system)
        cache.set(cache_key, events)

    if not events:
        raise HTTPException(status_code=404, detail=f"No events found for app: {app_name}")

    # Sort
    if order == "desc":
        events = sorted(events, key=lambda e: e.start_time, reverse=True)

    # Paginate
    total_events = len(events)
    total_pages = math.ceil(total_events / limit)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    page_events = events[start_idx:end_idx]

    return TimelineResponse(
        start_date=start_date,
        end_date=end_date or datetime.now().strftime("%Y-%m-%d"),
        page=page,
        limit=limit,
        total_events=total_events,
        total_pages=total_pages,
        events=[
            EventSchema(
                app_name=e.app_name,
                bundle_id=e.bundle_id,
                start_time=e.start_time,
                end_time=e.end_time,
                duration_seconds=e.duration_seconds,
            )
            for e in page_events
        ],
    )
