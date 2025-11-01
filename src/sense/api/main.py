"""FastAPI application."""

from fastapi import FastAPI

from sense.api.routes import switches, timeline

app = FastAPI(
    title="Sense API",
    description="macOS activity tracker using KnowledgeC database",
    version="0.1.0",
)

app.include_router(timeline.router, prefix="/api")
app.include_router(switches.router, prefix="/api")


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
