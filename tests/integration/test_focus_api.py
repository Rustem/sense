"""Integration tests for focus sessions API."""

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from sense.api.main import app

client = TestClient(app)


def test_focus_missing_start_date() -> None:
    """Test focus returns 422 when start_date is missing."""
    response = client.get("/api/focus")
    assert response.status_code == 422


def test_focus_invalid_date_format() -> None:
    """Test focus returns 400 for invalid date format."""
    response = client.get("/api/focus?start_date=invalid")
    assert response.status_code == 400
    assert "Invalid date format" in response.json()["detail"]


def test_focus_date_range_too_large() -> None:
    """Test focus returns 400 when date range exceeds limit."""
    start = datetime.now() - timedelta(days=10)
    end = datetime.now()
    response = client.get(
        f"/api/focus?start_date={start.strftime('%Y-%m-%d')}&end_date={end.strftime('%Y-%m-%d')}"
    )
    assert response.status_code == 400
    assert "Date range cannot exceed" in response.json()["detail"]


def test_focus_end_before_start() -> None:
    """Test focus returns 400 when end_date is before start_date."""
    start = datetime.now()
    end = start - timedelta(days=1)
    response = client.get(
        f"/api/focus?start_date={start.strftime('%Y-%m-%d')}&end_date={end.strftime('%Y-%m-%d')}"
    )
    assert response.status_code == 400
    assert "end_date must be >= start_date" in response.json()["detail"]


def test_focus_pagination_params() -> None:
    """Test focus validates pagination parameters."""
    start = datetime.now() - timedelta(days=1)

    # Invalid page
    response = client.get(f"/api/focus?start_date={start.strftime('%Y-%m-%d')}&page=0")
    assert response.status_code == 422

    # Invalid limit (too high)
    response = client.get(f"/api/focus?start_date={start.strftime('%Y-%m-%d')}&limit=2000")
    assert response.status_code == 422


def test_focus_order_validation() -> None:
    """Test focus validates order parameter."""
    start = datetime.now() - timedelta(days=1)

    response = client.get(f"/api/focus?start_date={start.strftime('%Y-%m-%d')}&order=invalid")
    assert response.status_code == 422


def test_focus_response_structure() -> None:
    """Test focus returns correct response structure."""
    start = datetime.now() - timedelta(days=1)
    response = client.get(f"/api/focus?start_date={start.strftime('%Y-%m-%d')}")

    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "start_date" in data
    assert "end_date" in data
    assert "page" in data
    assert "limit" in data
    assert "total_apps" in data
    assert "total_pages" in data
    assert "apps" in data
    assert isinstance(data["apps"], list)

    # Check app schema if any apps exist
    if data["apps"]:
        app = data["apps"][0]
        assert "app_name" in app
        assert "total_time_minutes" in app
        assert "total_sessions" in app
        assert "avg_session_minutes" in app
        assert "longest_session_minutes" in app
        assert "focus_sessions" in app
        assert isinstance(app["focus_sessions"], list)

        # Check session schema
        if app["focus_sessions"]:
            session = app["focus_sessions"][0]
            assert "start" in session
            assert "end" in session
            assert "duration_minutes" in session


def test_focus_ordering() -> None:
    """Test focus ordering by total_time_minutes."""
    start = datetime.now() - timedelta(days=1)

    # Descending order (default)
    response_desc = client.get(f"/api/focus?start_date={start.strftime('%Y-%m-%d')}&order=desc")
    assert response_desc.status_code == 200

    # Ascending order
    response_asc = client.get(f"/api/focus?start_date={start.strftime('%Y-%m-%d')}&order=asc")
    assert response_asc.status_code == 200

    # Verify ordering if apps exist
    data_desc = response_desc.json()
    if len(data_desc["apps"]) > 1:
        times_desc = [app["total_time_minutes"] for app in data_desc["apps"]]
        assert times_desc == sorted(times_desc, reverse=True)

    data_asc = response_asc.json()
    if len(data_asc["apps"]) > 1:
        times_asc = [app["total_time_minutes"] for app in data_asc["apps"]]
        assert times_asc == sorted(times_asc)


def test_focus_pagination() -> None:
    """Test focus pagination."""
    start = datetime.now() - timedelta(days=1)

    # Get first page with limit 5
    response = client.get(f"/api/focus?start_date={start.strftime('%Y-%m-%d')}&page=1&limit=5")
    assert response.status_code == 200
    data = response.json()

    assert data["page"] == 1
    assert data["limit"] == 5
    assert len(data["apps"]) <= 5


def test_app_focus_response_structure() -> None:
    """Test app-specific focus endpoint."""
    start = datetime.now() - timedelta(days=1)
    app_name = "com.apple.Safari"

    response = client.get(f"/api/focus/{app_name}?start_date={start.strftime('%Y-%m-%d')}")

    # Should be 200 (with data) or 404 (no data for this app)
    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()

        # Check response structure
        assert data["app_name"] == app_name
        assert "start_date" in data
        assert "end_date" in data
        assert "total_time_minutes" in data
        assert "total_sessions" in data
        assert "avg_session_minutes" in data
        assert "longest_session_minutes" in data
        assert "shortest_session_minutes" in data
        assert "focus_sessions" in data
        assert isinstance(data["focus_sessions"], list)

        # Validate metrics
        assert data["total_time_minutes"] > 0
        assert data["total_sessions"] > 0
        assert len(data["focus_sessions"]) == data["total_sessions"]

        # Check session schema
        if data["focus_sessions"]:
            session = data["focus_sessions"][0]
            assert "start" in session
            assert "end" in session
            assert "duration_minutes" in session


def test_app_focus_not_found() -> None:
    """Test app focus returns 404 for non-existent app."""
    start = datetime.now() - timedelta(days=1)
    app_name = "com.nonexistent.app.that.does.not.exist"

    response = client.get(f"/api/focus/{app_name}?start_date={start.strftime('%Y-%m-%d')}")
    assert response.status_code == 404
    assert "No focus data found for app" in response.json()["detail"]


def test_focus_sessions_sorted_desc() -> None:
    """Test that focus sessions are sorted by start time descending."""
    start = datetime.now() - timedelta(days=1)

    response = client.get(f"/api/focus?start_date={start.strftime('%Y-%m-%d')}")
    assert response.status_code == 200
    data = response.json()

    # Check each app's sessions are sorted
    for app_data in data["apps"]:
        if len(app_data["focus_sessions"]) > 1:
            session_times = [session["start"] for session in app_data["focus_sessions"]]
            assert session_times == sorted(session_times, reverse=True)


def test_focus_metrics_accuracy() -> None:
    """Test that focus metrics are calculated correctly."""
    start = datetime.now() - timedelta(days=1)

    response = client.get(f"/api/focus?start_date={start.strftime('%Y-%m-%d')}")
    assert response.status_code == 200
    data = response.json()

    for app_data in data["apps"]:
        sessions = app_data["focus_sessions"]
        if sessions:
            # Verify total_time_minutes
            calculated_total = sum(s["duration_minutes"] for s in sessions)
            assert abs(app_data["total_time_minutes"] - calculated_total) < 0.01

            # Verify total_sessions
            assert app_data["total_sessions"] == len(sessions)

            # Verify avg_session_minutes
            expected_avg = calculated_total / len(sessions)
            assert abs(app_data["avg_session_minutes"] - expected_avg) < 0.01

            # Verify longest_session_minutes
            expected_longest = max(s["duration_minutes"] for s in sessions)
            assert abs(app_data["longest_session_minutes"] - expected_longest) < 0.01
