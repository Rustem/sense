"""Shared utilities for API routes."""

import math
from collections.abc import Callable
from datetime import datetime
from typing import Any, TypeVar

from fastapi import HTTPException

from sense.config import settings

T = TypeVar("T")


def parse_date(date_str: str) -> datetime:
    """Parse YYYY-MM-DD date string to datetime."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {date_str}") from e


def validate_date_range(start: datetime, end: datetime) -> None:
    """Validate date range is within limits."""
    if end < start:
        raise HTTPException(status_code=400, detail="end_date must be >= start_date")

    delta = (end - start).days
    if delta > settings.max_date_range_days:
        raise HTTPException(
            status_code=400,
            detail=f"Date range cannot exceed {settings.max_date_range_days} days",
        )


def sort_items(items: list[T], order: str, key: Callable[[T], Any]) -> list[T]:
    """Sort items by key in specified order.

    Args:
        items: List of items to sort
        order: Sort order ('asc' or 'desc')
        key: Function to extract sort key from item

    Returns:
        Sorted list
    """
    if order == "desc":
        return sorted(items, key=key, reverse=True)
    return items


def paginate(items: list[T], page: int, limit: int) -> tuple[list[T], int, int]:
    """Paginate items.

    Args:
        items: List of items to paginate
        page: Page number (1-indexed)
        limit: Items per page

    Returns:
        Tuple of (page_items, total_items, total_pages)
    """
    total_items = len(items)
    total_pages = math.ceil(total_items / limit)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    page_items = items[start_idx:end_idx]

    return page_items, total_items, total_pages
