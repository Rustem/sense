"""Focus sessions API routes."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from sense.api.utils import paginate, parse_date, sort_items, validate_date_range
from sense.config import settings
from sense.core.cache import InMemoryCache
from sense.core.filter_service import FilterService
from sense.core.focus_service import FocusService
from sense.core.knowledgec_repository import KnowledgeCRepository
from sense.models.schemas import (
    AppFocusDetailResponse,
    AppFocusSchema,
    FocusResponse,
    FocusSessionSchema,
)

router = APIRouter(prefix="/focus", tags=["focus"])

# Initialize services
repository = KnowledgeCRepository(settings.knowledgec_db_path)
filter_service = FilterService()
focus_service = FocusService()
cache = InMemoryCache(ttl_seconds=settings.cache_ttl_seconds)


@router.get("", response_model=FocusResponse)
def get_focus(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="End date (YYYY-MM-DD), defaults to now"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(100, ge=1, le=1000, description="Apps per page"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order by total_time_minutes"),
) -> FocusResponse:
    """Get focus sessions across all apps."""
    start = parse_date(start_date)
    end = parse_date(end_date) if end_date else datetime.now()
    validate_date_range(start, end)

    # Generate cache key
    cache_key = f"focus:{start_date}:{end_date}"
    cached = cache.get(cache_key)
    if cached:
        app_sessions = cached
    else:
        # Query database
        events = repository.get_events(start, end)
        # Apply filters (exclude system apps by default)
        events = filter_service.filter_events(events, include_system=False)
        # Calculate focus sessions
        app_sessions = focus_service.calculate_focus_sessions(
            events, settings.focus_session_gap_minutes
        )
        cache.set(cache_key, app_sessions)

    # Build response data
    apps_data = []
    for app_name, sessions in app_sessions.items():
        if not sessions:
            continue

        total_time = sum(s.duration_minutes for s in sessions)
        total_sessions = len(sessions)
        avg_session = total_time / total_sessions if total_sessions > 0 else 0
        longest_session = max(s.duration_minutes for s in sessions)

        apps_data.append(
            {
                "app_name": app_name,
                "total_time_minutes": total_time,
                "total_sessions": total_sessions,
                "avg_session_minutes": avg_session,
                "longest_session_minutes": longest_session,
                "focus_sessions": sessions,
            }
        )

    # Sort by total_time_minutes
    apps_data = sort_items(apps_data, order, key=lambda a: a["total_time_minutes"])

    # Paginate
    page_apps, total_apps, total_pages = paginate(apps_data, page, limit)

    return FocusResponse(
        start_date=start_date,
        end_date=end_date or datetime.now().strftime("%Y-%m-%d"),
        page=page,
        limit=limit,
        total_apps=total_apps,
        total_pages=total_pages,
        apps=[
            AppFocusSchema(
                app_name=app["app_name"],
                total_time_minutes=app["total_time_minutes"],
                total_sessions=app["total_sessions"],
                avg_session_minutes=app["avg_session_minutes"],
                longest_session_minutes=app["longest_session_minutes"],
                focus_sessions=[
                    FocusSessionSchema(
                        start=s.start, end=s.end, duration_minutes=s.duration_minutes
                    )
                    for s in app["focus_sessions"]
                ],
            )
            for app in page_apps
        ],
    )


@router.get("/{app_name}", response_model=AppFocusDetailResponse)
def get_app_focus(
    app_name: str,
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="End date (YYYY-MM-DD), defaults to now"),
) -> AppFocusDetailResponse:
    """Get detailed focus sessions for a specific app."""
    start = parse_date(start_date)
    end = parse_date(end_date) if end_date else datetime.now()
    validate_date_range(start, end)

    # Generate cache key
    cache_key = f"focus:{app_name}:{start_date}:{end_date}"
    cached = cache.get(cache_key)
    if cached:
        sessions = cached
    else:
        # Query database
        events = repository.get_events(start, end)
        # Apply filters
        events = filter_service.filter_events(events, include_system=False)
        # Calculate focus sessions for all apps
        app_sessions = focus_service.calculate_focus_sessions(
            events, settings.focus_session_gap_minutes
        )
        # Get sessions for specific app
        sessions = focus_service.get_app_sessions(app_sessions, app_name)
        cache.set(cache_key, sessions)

    if not sessions:
        raise HTTPException(status_code=404, detail=f"No focus data found for app: {app_name}")

    # Calculate metrics
    total_time = sum(s.duration_minutes for s in sessions)
    total_sessions = len(sessions)
    avg_session = total_time / total_sessions if total_sessions > 0 else 0
    longest_session = max(s.duration_minutes for s in sessions)
    shortest_session = min(s.duration_minutes for s in sessions)

    return AppFocusDetailResponse(
        app_name=app_name,
        start_date=start_date,
        end_date=end_date or datetime.now().strftime("%Y-%m-%d"),
        total_time_minutes=total_time,
        total_sessions=total_sessions,
        avg_session_minutes=avg_session,
        longest_session_minutes=longest_session,
        shortest_session_minutes=shortest_session,
        focus_sessions=[
            FocusSessionSchema(start=s.start, end=s.end, duration_minutes=s.duration_minutes)
            for s in sessions
        ],
    )
