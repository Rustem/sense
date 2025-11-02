"""Interruptions API routes."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from sense.api.utils import paginate, parse_date, sort_items, validate_date_range
from sense.config import settings
from sense.core.cache import InMemoryCache
from sense.core.filter_service import FilterService
from sense.core.interruption_service import InterruptionService
from sense.core.knowledgec_repository import KnowledgeCRepository
from sense.models.schemas import (
    AppInterruptionsResponse,
    AppInterruptionSummary,
    InterruptionSchema,
    InterruptionsResponse,
)

router = APIRouter(prefix="/interruptions", tags=["interruptions"])

# Initialize services
repository = KnowledgeCRepository(settings.knowledgec_db_path)
filter_service = FilterService()
interruption_service = InterruptionService()
cache = InMemoryCache(ttl_seconds=settings.cache_ttl_seconds)


@router.get("", response_model=InterruptionsResponse)
def get_interruptions(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="End date (YYYY-MM-DD), defaults to now"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(100, ge=1, le=1000, description="Interruptions per page"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order by time"),
    max_interruption_seconds: int | None = Query(
        None, ge=1, description="Max duration for interruption (default: 300s)"
    ),
) -> InterruptionsResponse:
    """Get all interruptions across all apps."""
    start = parse_date(start_date)
    end = parse_date(end_date) if end_date else datetime.now()
    validate_date_range(start, end)

    max_seconds = max_interruption_seconds or settings.max_interruption_seconds

    # Generate cache key
    cache_key = f"interruptions:{start_date}:{end_date}:{max_seconds}"
    cached = cache.get(cache_key)
    if cached:
        interruptions, summary = cached
    else:
        # Query database
        events = repository.get_events(start, end)
        # Apply filters (exclude system apps by default)
        events = filter_service.filter_events(events, include_system=False)
        # Calculate interruptions
        interruptions = interruption_service.calculate_interruptions(events, max_seconds)
        # Calculate summary
        summary = interruption_service.calculate_summary(interruptions)
        cache.set(cache_key, (interruptions, summary))

    # Sort and paginate
    interruptions = sort_items(interruptions, order, key=lambda i: i.time)
    page_interruptions, total_interruptions, total_pages = paginate(interruptions, page, limit)

    # Build summary response
    summary_response = {
        "most_interrupting_apps": [
            AppInterruptionSummary(**app) for app in summary["most_interrupting_apps"]
        ],
        "most_interrupted_apps": [
            AppInterruptionSummary(**app) for app in summary["most_interrupted_apps"]
        ],
    }

    return InterruptionsResponse(
        start_date=start_date,
        end_date=end_date or datetime.now().strftime("%Y-%m-%d"),
        max_interruption_seconds=max_seconds,
        page=page,
        limit=limit,
        total_interruptions=total_interruptions,
        total_pages=total_pages,
        interruptions=[
            InterruptionSchema(
                time=i.time,
                interrupted_app=i.interrupted_app,
                interrupting_app=i.interrupting_app,
                duration_seconds=i.duration_seconds,
                gap_before_seconds=i.gap_before_seconds,
                gap_after_seconds=i.gap_after_seconds,
            )
            for i in page_interruptions
        ],
        summary=summary_response,
    )


@router.get("/{app_name}", response_model=AppInterruptionsResponse)
def get_app_interruptions(
    app_name: str,
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="End date (YYYY-MM-DD), defaults to now"),
    role: str = Query(
        "both",
        pattern="^(interrupted|interrupting|both)$",
        description="Filter by role: interrupted, interrupting, or both",
    ),
    max_interruption_seconds: int | None = Query(
        None, ge=1, description="Max duration for interruption (default: 300s)"
    ),
) -> AppInterruptionsResponse:
    """Get interruptions for a specific app."""
    start = parse_date(start_date)
    end = parse_date(end_date) if end_date else datetime.now()
    validate_date_range(start, end)

    max_seconds = max_interruption_seconds or settings.max_interruption_seconds

    # Generate cache key
    cache_key = f"interruptions:{app_name}:{start_date}:{end_date}:{role}:{max_seconds}"
    cached = cache.get(cache_key)
    if cached:
        interruptions = cached
    else:
        # Query database
        events = repository.get_events(start, end)
        # Apply filters
        events = filter_service.filter_events(events, include_system=False)
        # Calculate all interruptions
        all_interruptions = interruption_service.calculate_interruptions(events, max_seconds)
        # Filter by app
        interruptions = interruption_service.filter_by_app(all_interruptions, app_name, role)
        cache.set(cache_key, interruptions)

    if not interruptions:
        raise HTTPException(status_code=404, detail=f"No interruptions found for app: {app_name}")

    # Calculate avg duration
    avg_duration = sum(i.duration_seconds for i in interruptions) / len(interruptions)

    return AppInterruptionsResponse(
        app_name=app_name,
        start_date=start_date,
        end_date=end_date or datetime.now().strftime("%Y-%m-%d"),
        max_interruption_seconds=max_seconds,
        role=role,
        total_interruptions=len(interruptions),
        avg_duration_seconds=avg_duration,
        interruptions=[
            InterruptionSchema(
                time=i.time,
                interrupted_app=i.interrupted_app,
                interrupting_app=i.interrupting_app,
                duration_seconds=i.duration_seconds,
                gap_before_seconds=i.gap_before_seconds,
                gap_after_seconds=i.gap_after_seconds,
            )
            for i in interruptions
        ],
    )
