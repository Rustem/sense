"""Application configuration."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Database
    knowledgec_db_path: Path = Path(__file__).parent.parent.parent / "experiment" / "knowledgeC.db"

    # Cache
    cache_ttl_seconds: int = 60

    # Pagination
    default_page_size: int = 100
    max_page_size: int = 1000

    # Date range limits
    max_date_range_days: int = 7

    # Focus sessions
    focus_session_gap_minutes: float = 5.0

    # Interruptions
    max_interruption_seconds: int = 300  # 5 minutes

    # Filters
    global_blocked_domains: list[str] = [
        "pornhub.com",
        "xvideos.com",
        "xnxx.com",
    ]

    system_apps: list[str] = [
        "com.apple.quicklook.QuickLookUIService",
        "com.apple.archiveutility",
        "com.apple.systempreferences",
        "com.apple.Mouse-Settings.extension",
    ]


settings = Settings()
