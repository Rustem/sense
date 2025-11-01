"""Filter configuration models."""

from pydantic import BaseModel


class FilterConfig(BaseModel):
    """Filter configuration for excluding apps/domains."""

    global_blocked: list[str] = []
    system_apps: list[str] = []
    user_excluded: list[str] = []
