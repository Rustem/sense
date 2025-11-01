"""Integration tests for timeline API."""

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from sense.api.main import app

client = TestClient(app)


def test_health_check() -> None:
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_timeline_missing_start_date() -> None:
    """Test timeline returns 422 when start_date is missing."""
    response = client.get("/api/timeline")
    assert response.status_code == 422


def test_timeline_invalid_date_format() -> None:
    """Test timeline returns 400 for invalid date format."""
    response = client.get("/api/timeline?start_date=invalid")
    assert response.status_code == 400
    assert "Invalid date format" in response.json()["detail"]


def test_timeline_date_range_too_large() -> None:
    """Test timeline returns 400 when date range exceeds limit."""
    start = datetime.now() - timedelta(days=10)
    end = datetime.now()
    response = client.get(
        f"/api/timeline?start_date={start.strftime('%Y-%m-%d')}&end_date={end.strftime('%Y-%m-%d')}"
    )
    assert response.status_code == 400
    assert "Date range cannot exceed" in response.json()["detail"]


def test_timeline_end_before_start() -> None:
    """Test timeline returns 400 when end_date is before start_date."""
    start = datetime.now()
    end = start - timedelta(days=1)
    response = client.get(
        f"/api/timeline?start_date={start.strftime('%Y-%m-%d')}&end_date={end.strftime('%Y-%m-%d')}"
    )
    assert response.status_code == 400
    assert "end_date must be >= start_date" in response.json()["detail"]


def test_timeline_pagination_params() -> None:
    """Test timeline validates pagination parameters."""
    start = datetime.now() - timedelta(days=1)

    # Invalid page
    response = client.get(f"/api/timeline?start_date={start.strftime('%Y-%m-%d')}&page=0")
    assert response.status_code == 422

    # Invalid limit (too high)
    response = client.get(f"/api/timeline?start_date={start.strftime('%Y-%m-%d')}&limit=2000")
    assert response.status_code == 422


def test_timeline_order_validation() -> None:
    """Test timeline validates order parameter."""
    start = datetime.now() - timedelta(days=1)

    response = client.get(f"/api/timeline?start_date={start.strftime('%Y-%m-%d')}&order=invalid")
    assert response.status_code == 422
