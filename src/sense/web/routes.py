"""Web dashboard routes."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from sense.config import settings
from sense.core.knowledgec_repository import KnowledgeCRepository

router = APIRouter()
templates = Jinja2Templates(directory="src/sense/web/templates")

# Initialize repository
repository = KnowledgeCRepository(settings.knowledgec_db_path)


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    """Main dashboard page with activity dates."""
    # Get dates with activity (last 90 days)
    end = datetime.now()
    start = end - timedelta(days=90)
    events = repository.get_events(start, end)

    # Extract unique dates
    dates_with_activity = set()
    for event in events:
        date_str = event.start_time.strftime("%Y-%m-%d")
        dates_with_activity.add(date_str)

    # Sort descending (most recent first)
    activity_dates = sorted(dates_with_activity, reverse=True)

    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "activity_dates": activity_dates}
    )
