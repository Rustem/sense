"""Integration tests for context switches API."""

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from sense.api.main import app

client = TestClient(app)


def test_switches_missing_start_date() -> None:
    """Test switches returns 422 when start_date is missing."""
    response = client.get("/api/switches")
    assert response.status_code == 422


def test_switches_invalid_date_format() -> None:
    """Test switches returns 400 for invalid date format."""
    response = client.get("/api/switches?start_date=invalid")
    assert response.status_code == 400
    assert "Invalid date format" in response.json()["detail"]


def test_switches_date_range_too_large() -> None:
    """Test switches returns 400 when date range exceeds limit."""
    start = datetime.now() - timedelta(days=10)
    end = datetime.now()
    response = client.get(
        f"/api/switches?start_date={start.strftime('%Y-%m-%d')}&end_date={end.strftime('%Y-%m-%d')}"
    )
    assert response.status_code == 400
    assert "Date range cannot exceed" in response.json()["detail"]


def test_switches_end_before_start() -> None:
    """Test switches returns 400 when end_date is before start_date."""
    start = datetime.now()
    end = start - timedelta(days=1)
    response = client.get(
        f"/api/switches?start_date={start.strftime('%Y-%m-%d')}&end_date={end.strftime('%Y-%m-%d')}"
    )
    assert response.status_code == 400
    assert "end_date must be >= start_date" in response.json()["detail"]


def test_switches_pagination_params() -> None:
    """Test switches validates pagination parameters."""
    start = datetime.now() - timedelta(days=1)

    # Invalid page
    response = client.get(f"/api/switches?start_date={start.strftime('%Y-%m-%d')}&page=0")
    assert response.status_code == 422

    # Invalid limit (too high)
    response = client.get(f"/api/switches?start_date={start.strftime('%Y-%m-%d')}&limit=2000")
    assert response.status_code == 422


def test_switches_order_validation() -> None:
    """Test switches validates order parameter."""
    start = datetime.now() - timedelta(days=1)

    response = client.get(f"/api/switches?start_date={start.strftime('%Y-%m-%d')}&order=invalid")
    assert response.status_code == 422


def test_switches_min_gap_validation() -> None:
    """Test switches validates min_gap_seconds parameter."""
    start = datetime.now() - timedelta(days=1)

    # Negative gap should fail
    response = client.get(
        f"/api/switches?start_date={start.strftime('%Y-%m-%d')}&min_gap_seconds=-1"
    )
    assert response.status_code == 422


def test_switches_response_structure() -> None:
    """Test switches returns correct response structure."""
    start = datetime.now() - timedelta(days=1)
    response = client.get(f"/api/switches?start_date={start.strftime('%Y-%m-%d')}")

    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "start_date" in data
    assert "end_date" in data
    assert "page" in data
    assert "limit" in data
    assert "total_switches" in data
    assert "total_pages" in data
    assert "switches" in data
    assert isinstance(data["switches"], list)

    # Check switch schema if any switches exist
    if data["switches"]:
        switch = data["switches"][0]
        assert "from_app" in switch
        assert "to_app" in switch
        assert "time" in switch
        assert "gap_seconds" in switch


def test_switches_with_min_gap() -> None:
    """Test switches filtering by minimum gap."""
    start = datetime.now() - timedelta(days=1)
    response = client.get(
        f"/api/switches?start_date={start.strftime('%Y-%m-%d')}&min_gap_seconds=10"
    )

    assert response.status_code == 200
    data = response.json()

    # All switches should have gap >= 10 seconds
    for switch in data["switches"]:
        assert switch["gap_seconds"] >= 10


def test_switches_with_system_apps() -> None:
    """Test switches with include_system parameter."""
    start = datetime.now() - timedelta(days=1)

    # Without system apps
    response_no_sys = client.get(
        f"/api/switches?start_date={start.strftime('%Y-%m-%d')}&include_system=false"
    )
    assert response_no_sys.status_code == 200

    # With system apps
    response_with_sys = client.get(
        f"/api/switches?start_date={start.strftime('%Y-%m-%d')}&include_system=true"
    )
    assert response_with_sys.status_code == 200


def test_switches_ordering() -> None:
    """Test switches ordering."""
    start = datetime.now() - timedelta(days=1)

    # Descending order (default)
    response_desc = client.get(
        f"/api/switches?start_date={start.strftime('%Y-%m-%d')}&order=desc"
    )
    assert response_desc.status_code == 200

    # Ascending order
    response_asc = client.get(
        f"/api/switches?start_date={start.strftime('%Y-%m-%d')}&order=asc"
    )
    assert response_asc.status_code == 200

    # Verify ordering if switches exist
    data_desc = response_desc.json()
    if len(data_desc["switches"]) > 1:
        times_desc = [switch["time"] for switch in data_desc["switches"]]
        assert times_desc == sorted(times_desc, reverse=True)

    data_asc = response_asc.json()
    if len(data_asc["switches"]) > 1:
        times_asc = [switch["time"] for switch in data_asc["switches"]]
        assert times_asc == sorted(times_asc)


def test_app_switches_response_structure() -> None:
    """Test app-specific switches endpoint."""
    start = datetime.now() - timedelta(days=1)
    app_name = "com.apple.Safari"

    response = client.get(f"/api/switches/{app_name}?start_date={start.strftime('%Y-%m-%d')}")

    # Should be 200 (with data) or 404 (no data for this app)
    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert "switches" in data

        # All switches should involve the specified app
        for switch in data["switches"]:
            assert switch["from_app"] == app_name or switch["to_app"] == app_name


def test_app_switches_not_found() -> None:
    """Test app switches returns 404 for non-existent app."""
    start = datetime.now() - timedelta(days=1)
    app_name = "com.nonexistent.app.that.does.not.exist"

    response = client.get(f"/api/switches/{app_name}?start_date={start.strftime('%Y-%m-%d')}")
    assert response.status_code == 404
    assert "No switches found for app" in response.json()["detail"]
