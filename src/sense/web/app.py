"""Web dashboard configuration."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from sense.web import routes


def configure_web(app: FastAPI) -> None:
    """Configure web dashboard routes and static files.

    Args:
        app: FastAPI application instance
    """
    # Mount static files
    static_path = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

    # Include web routes
    app.include_router(routes.router)
