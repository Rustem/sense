"""FastAPI application."""

from fastapi import FastAPI

from sense.api.routes import focus, interruptions, switches, timeline
from sense.web.app import configure_web

app = FastAPI(
    title="Sense API",
    description="macOS activity tracker using KnowledgeC database",
    version="0.1.0",
)

# API routes
app.include_router(timeline.router, prefix="/api")
app.include_router(switches.router, prefix="/api")
app.include_router(focus.router, prefix="/api")
app.include_router(interruptions.router, prefix="/api")

# Web dashboard
configure_web(app)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
