"""Integration tests for interruptions API."""

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from sense.api.main import app

client = TestClient(app)


def test_interruptions_missing_start_date() -> None:
    """Test interruptions returns 422 when start_date is missing."""
    response = client.get("/api/interruptions")
    assert response.status_code == 422


def test_interruptions_invalid_date_format() -> None:
    """Test interruptions returns 400 for invalid date format."""
    response = client.get("/api/interruptions?start_date=invalid")
    assert response.status_code == 400
    assert "Invalid date format" in response.json()["detail"]


def test_interruptions_date_range_too_large() -> None:
    """Test interruptions returns 400 when date range exceeds limit."""
    start = datetime.now() - timedelta(days=10)
    end = datetime.now()
    response = client.get(
        f"/api/interruptions?start_date={start.strftime('%Y-%m-%d')}&end_date={end.strftime('%Y-%m-%d')}"
    )
    assert response.status_code == 400
    assert "Date range cannot exceed" in response.json()["detail"]


def test_interruptions_end_before_start() -> None:
    """Test interruptions returns 400 when end_date is before start_date."""
    start = datetime.now()
    end = start - timedelta(days=1)
    response = client.get(
        f"/api/interruptions?start_date={start.strftime('%Y-%m-%d')}&end_date={end.strftime('%Y-%m-%d')}"
    )
    assert response.status_code == 400
    assert "end_date must be >= start_date" in response.json()["detail"]


def test_interruptions_pagination_params() -> None:
    """Test interruptions validates pagination parameters."""
    start = datetime.now() - timedelta(days=1)

    # Invalid page
    response = client.get(f"/api/interruptions?start_date={start.strftime('%Y-%m-%d')}&page=0")
    assert response.status_code == 422

    # Invalid limit (too high)
    response = client.get(
        f"/api/interruptions?start_date={start.strftime('%Y-%m-%d')}&limit=2000"
    )
    assert response.status_code == 422


def test_interruptions_order_validation() -> None:
    """Test interruptions validates order parameter."""
    start = datetime.now() - timedelta(days=1)

    response = client.get(
        f"/api/interruptions?start_date={start.strftime('%Y-%m-%d')}&order=invalid"
    )
    assert response.status_code == 422


def test_interruptions_max_seconds_validation() -> None:
    """Test interruptions validates max_interruption_seconds parameter."""
    start = datetime.now() - timedelta(days=1)

    # Negative value should fail
    response = client.get(
        f"/api/interruptions?start_date={start.strftime('%Y-%m-%d')}&max_interruption_seconds=-1"
    )
    assert response.status_code == 422


def test_interruptions_response_structure() -> None:
    """Test interruptions returns correct response structure."""
    start = datetime.now() - timedelta(days=1)
    response = client.get(f"/api/interruptions?start_date={start.strftime('%Y-%m-%d')}")

    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "start_date" in data
    assert "end_date" in data
    assert "max_interruption_seconds" in data
    assert "page" in data
    assert "limit" in data
    assert "total_interruptions" in data
    assert "total_pages" in data
    assert "interruptions" in data
    assert "summary" in data
    assert isinstance(data["interruptions"], list)

    # Check summary structure
    assert "most_interrupting_apps" in data["summary"]
    assert "most_interrupted_apps" in data["summary"]
    assert isinstance(data["summary"]["most_interrupting_apps"], list)
    assert isinstance(data["summary"]["most_interrupted_apps"], list)

    # Check interruption schema if any interruptions exist
    if data["interruptions"]:
        interruption = data["interruptions"][0]
        assert "time" in interruption
        assert "interrupted_app" in interruption
        assert "interrupting_app" in interruption
        assert "duration_seconds" in interruption
        assert "gap_before_seconds" in interruption
        assert "gap_after_seconds" in interruption


def test_interruptions_with_custom_max_seconds() -> None:
    """Test interruptions with custom max_interruption_seconds."""
    start = datetime.now() - timedelta(days=1)

    # With 60 seconds max
    response_60 = client.get(
        f"/api/interruptions?start_date={start.strftime('%Y-%m-%d')}&max_interruption_seconds=60"
    )
    assert response_60.status_code == 200
    data_60 = response_60.json()
    assert data_60["max_interruption_seconds"] == 60

    # With 300 seconds max (default)
    response_300 = client.get(
        f"/api/interruptions?start_date={start.strftime('%Y-%m-%d')}&max_interruption_seconds=300"
    )
    assert response_300.status_code == 200
    data_300 = response_300.json()
    assert data_300["max_interruption_seconds"] == 300


def test_interruptions_ordering() -> None:
    """Test interruptions ordering by time."""
    start = datetime.now() - timedelta(days=1)

    # Descending order (default)
    response_desc = client.get(
        f"/api/interruptions?start_date={start.strftime('%Y-%m-%d')}&order=desc"
    )
    assert response_desc.status_code == 200

    # Ascending order
    response_asc = client.get(
        f"/api/interruptions?start_date={start.strftime('%Y-%m-%d')}&order=asc"
    )
    assert response_asc.status_code == 200

    # Verify ordering if interruptions exist
    data_desc = response_desc.json()
    if len(data_desc["interruptions"]) > 1:
        times_desc = [i["time"] for i in data_desc["interruptions"]]
        assert times_desc == sorted(times_desc, reverse=True)

    data_asc = response_asc.json()
    if len(data_asc["interruptions"]) > 1:
        times_asc = [i["time"] for i in data_asc["interruptions"]]
        assert times_asc == sorted(times_asc)


def test_interruptions_pagination() -> None:
    """Test interruptions pagination."""
    start = datetime.now() - timedelta(days=1)

    # Get first page with limit 5
    response = client.get(
        f"/api/interruptions?start_date={start.strftime('%Y-%m-%d')}&page=1&limit=5"
    )
    assert response.status_code == 200
    data = response.json()

    assert data["page"] == 1
    assert data["limit"] == 5
    assert len(data["interruptions"]) <= 5


def test_interruptions_summary_structure() -> None:
    """Test interruptions summary has correct structure."""
    start = datetime.now() - timedelta(days=1)
    response = client.get(f"/api/interruptions?start_date={start.strftime('%Y-%m-%d')}")

    assert response.status_code == 200
    data = response.json()

    summary = data["summary"]

    # Check summary app structure if apps exist
    if summary["most_interrupting_apps"]:
        app = summary["most_interrupting_apps"][0]
        assert "app_name" in app
        assert "count" in app
        assert "avg_duration_seconds" in app

    if summary["most_interrupted_apps"]:
        app = summary["most_interrupted_apps"][0]
        assert "app_name" in app
        assert "count" in app
        assert "avg_duration_seconds" in app


def test_app_interruptions_response_structure() -> None:
    """Test app-specific interruptions endpoint."""
    start = datetime.now() - timedelta(days=1)
    app_name = "web"

    response = client.get(
        f"/api/interruptions/{app_name}?start_date={start.strftime('%Y-%m-%d')}"
    )

    # Should be 200 (with data) or 404 (no data for this app)
    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()

        # Check response structure
        assert data["app_name"] == app_name
        assert "start_date" in data
        assert "end_date" in data
        assert "max_interruption_seconds" in data
        assert "role" in data
        assert "total_interruptions" in data
        assert "avg_duration_seconds" in data
        assert "interruptions" in data
        assert isinstance(data["interruptions"], list)

        # Validate metrics
        assert data["total_interruptions"] >= 0
        assert data["avg_duration_seconds"] >= 0
        assert len(data["interruptions"]) == data["total_interruptions"]


def test_app_interruptions_not_found() -> None:
    """Test app interruptions returns 404 for non-existent app."""
    start = datetime.now() - timedelta(days=1)
    app_name = "com.nonexistent.app.that.does.not.exist"

    response = client.get(
        f"/api/interruptions/{app_name}?start_date={start.strftime('%Y-%m-%d')}"
    )
    assert response.status_code == 404
    assert "No interruptions found for app" in response.json()["detail"]


def test_app_interruptions_role_filter() -> None:
    """Test app interruptions role parameter."""
    start = datetime.now() - timedelta(days=1)
    app_name = "web"

    # Test each role
    for role in ["interrupted", "interrupting", "both"]:
        response = client.get(
            f"/api/interruptions/{app_name}?start_date={start.strftime('%Y-%m-%d')}&role={role}"
        )
        # Should be 200 or 404
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert data["role"] == role


def test_app_interruptions_invalid_role() -> None:
    """Test app interruptions with invalid role parameter."""
    start = datetime.now() - timedelta(days=1)
    app_name = "web"

    response = client.get(
        f"/api/interruptions/{app_name}?start_date={start.strftime('%Y-%m-%d')}&role=invalid"
    )
    assert response.status_code == 422
