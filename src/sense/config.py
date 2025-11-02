"""Application configuration."""

import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Environment
    environment: str = os.getenv("SENSE_ENV", "dev")

    # Database
    @property
    def knowledgec_db_path(self) -> Path:
        """Get database path based on environment."""
        if self.environment == "prod":
            # Production: use real macOS KnowledgeC database
            return Path.home() / "Library" / "Application Support" / "Knowledge" / "knowledgeC.db"
        else:
            # Development: use synced copy in data/ directory
            return Path(__file__).parent.parent.parent / "data" / "knowledgeC.db"

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
