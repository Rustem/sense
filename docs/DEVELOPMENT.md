# Development Guide

## Setup

```bash
# Install dependencies
uv sync --all-extras

# Copy KnowledgeC database (optional, uses experiment/knowledgeC.db by default)
./scripts/copy_db.sh
```

## Development Workflow

### Run tests
```bash
uv run pytest
```

### Start API server
```bash
uv run uvicorn sense.api.main:app --reload
```

### Code quality checks
```bash
# Lint and format
uv run ruff check --fix .
uv run ruff format .

# Type check
uv run mypy src/
```

### Verify changes (run after every change)
```bash
uv run pytest && uv run ruff check --fix . && uv run mypy src/
```

## API Testing

```bash
# Health check
curl http://localhost:8000/health

# Get timeline
curl "http://localhost:8000/api/timeline?start_date=2025-10-15&limit=5"

# App-specific timeline
curl "http://localhost:8000/api/timeline/com.tinyspeck.slackmacgap?start_date=2025-10-10&end_date=2025-10-16"

# API docs
open http://localhost:8000/docs
```

## Project Structure

```
src/sense/
├── core/          # Business logic
├── api/           # FastAPI routes
├── web/           # Dashboard (future)
├── models/        # Pydantic schemas
└── config.py      # Settings

tests/
├── unit/          # Unit tests
└── integration/   # API tests
```

## Design Decisions

### App Identification: `app_name` vs `bundle_id`
- **Use `app_name` as primary identifier**: All services (context switches, focus sessions, interruptions) use `app_name` field instead of `bundle_id`
- **Rationale**:
  - KnowledgeC database stores the actual identifier in `app_name` (bundle ID for native apps, domain for web)
  - `bundle_id` field may be "web" for all events in some databases
  - `app_name` correctly identifies both native apps (e.g., "com.jetbrains.intellij") and web domains (e.g., "claude.ai")

### Focus Sessions
- **5-minute gap threshold**: Sessions are split when there's >5 minutes of inactivity
- **Configurable via `focus_session_gap_minutes`** in config.py
- **Rationale**: Aligns with Pomodoro technique, handles quick breaks (coffee, bathroom) without breaking sessions
- **No backend merging**: Sessions kept atomic; frontend can merge <5min gaps for display if needed
- **Sorted DESC by start time**: Most recent sessions first for timeline scrolling

### Interruptions Detection
- **Pattern: A → B (brief) → A**: Requires return to original app
- **Max duration: 5 minutes (300 seconds)**: Middle app must be ≤ threshold to count as interruption
- **Both criteria required**: Brief duration AND return pattern must both be true
- **Configurable via `max_interruption_seconds`** in config.py
- **Rationale**: 5 minutes covers 90%+ of notification-driven behavior; longer durations indicate intentional work

### Event Filtering
- **In-memory filtering** (not DB-level): Events are fetched from DB without filters, then filtered in Python
- **Rationale**: Required for context switch/interruption calculation, which needs all events to preserve temporal order and calculate accurate gaps

### API Consistency
- **Max 7-day range**: All endpoints enforce max date range to prevent performance issues
- **Pagination**: Standard `page` and `limit` parameters (default limit: 100, max: 1000)
- **Sorting**: Configurable `order` parameter (asc/desc)
- **System app filtering**: Excluded by default (can be included with `include_system` param where applicable)
- **Caching**: In-memory cache with 60-second TTL for all computed results

## Common Tasks

### Add new endpoint
1. Define Pydantic schemas in `models/`
2. Implement logic in `core/`
3. Add route in `api/routes/`
4. Write tests
5. Run verification

### Update dependencies
```bash
# Add new dependency
uv add package-name

# Update all
uv sync --all-extras
```
