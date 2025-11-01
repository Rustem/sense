"""Context switches API routes."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from sense.api.utils import paginate, parse_date, sort_items, validate_date_range
from sense.config import settings
from sense.core.cache import InMemoryCache
from sense.core.context_switch_service import ContextSwitchService
from sense.core.filter_service import FilterService
from sense.core.knowledgec_repository import KnowledgeCRepository
from sense.models.schemas import ContextSwitchSchema, SwitchesResponse

router = APIRouter(prefix="/switches", tags=["switches"])

# Initialize services
repository = KnowledgeCRepository(settings.knowledgec_db_path)
filter_service = FilterService()
switch_service = ContextSwitchService()
cache = InMemoryCache(ttl_seconds=settings.cache_ttl_seconds)


@router.get("", response_model=SwitchesResponse)
def get_switches(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="End date (YYYY-MM-DD), defaults to now"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(100, ge=1, le=1000, description="Switches per page"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    include_system: bool = Query(False, description="Include system apps"),
    min_gap_seconds: float | None = Query(None, ge=0, description="Minimum gap in seconds"),
) -> SwitchesResponse:
    """Get context switches between all apps."""
    start = parse_date(start_date)
    end = parse_date(end_date) if end_date else datetime.now()
    validate_date_range(start, end)

    # Generate cache key
    cache_key = f"switches:{start_date}:{end_date}:{include_system}:{min_gap_seconds}"
    cached = cache.get(cache_key)
    if cached:
        switches = cached
    else:
        # Query database
        events = repository.get_events(start, end)
        # Apply filters
        events = filter_service.filter_events(events, include_system=include_system)
        # Calculate switches
        switches = switch_service.calculate_switches(events, min_gap_seconds=min_gap_seconds)
        cache.set(cache_key, switches)

    # Sort and paginate
    switches = sort_items(switches, order, key=lambda s: s.time)
    page_switches, total_switches, total_pages = paginate(switches, page, limit)

    return SwitchesResponse(
        start_date=start_date,
        end_date=end_date or datetime.now().strftime("%Y-%m-%d"),
        page=page,
        limit=limit,
        total_switches=total_switches,
        total_pages=total_pages,
        switches=[
            ContextSwitchSchema(
                from_app=s.from_app,
                to_app=s.to_app,
                time=s.time,
                gap_seconds=s.gap_seconds,
            )
            for s in page_switches
        ],
    )


@router.get("/{app_name}", response_model=SwitchesResponse)
def get_app_switches(
    app_name: str,
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="End date (YYYY-MM-DD), defaults to now"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(100, ge=1, le=1000, description="Switches per page"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    include_system: bool = Query(False, description="Include system apps"),
    min_gap_seconds: float | None = Query(None, ge=0, description="Minimum gap in seconds"),
) -> SwitchesResponse:
    """Get context switches involving a specific app."""
    start = parse_date(start_date)
    end = parse_date(end_date) if end_date else datetime.now()
    validate_date_range(start, end)

    # Generate cache key
    cache_key = f"switches:{app_name}:{start_date}:{end_date}:{include_system}:{min_gap_seconds}"
    cached = cache.get(cache_key)
    if cached:
        switches = cached
    else:
        # Query database
        events = repository.get_events(start, end)
        # Apply filters
        events = filter_service.filter_events(events, include_system=include_system)
        # Calculate switches
        all_switches = switch_service.calculate_switches(events, min_gap_seconds=min_gap_seconds)
        # Filter by app
        switches = switch_service.filter_by_app(all_switches, app_name)
        cache.set(cache_key, switches)

    if not switches:
        raise HTTPException(status_code=404, detail=f"No switches found for app: {app_name}")

    # Sort and paginate
    switches = sort_items(switches, order, key=lambda s: s.time)
    page_switches, total_switches, total_pages = paginate(switches, page, limit)

    return SwitchesResponse(
        start_date=start_date,
        end_date=end_date or datetime.now().strftime("%Y-%m-%d"),
        page=page,
        limit=limit,
        total_switches=total_switches,
        total_pages=total_pages,
        switches=[
            ContextSwitchSchema(
                from_app=s.from_app,
                to_app=s.to_app,
                time=s.time,
                gap_seconds=s.gap_seconds,
            )
            for s in page_switches
        ],
    )
