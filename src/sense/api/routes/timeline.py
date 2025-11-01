"""Timeline API routes."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from sense.api.utils import paginate, parse_date, sort_items, validate_date_range
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

    # Sort and paginate
    events = sort_items(events, order, key=lambda e: e.start_time)
    page_events, total_events, total_pages = paginate(events, page, limit)

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

    # Sort and paginate
    events = sort_items(events, order, key=lambda e: e.start_time)
    page_events, total_events, total_pages = paginate(events, page, limit)

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
