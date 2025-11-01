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

### Event Filtering
- **In-memory filtering** (not DB-level): Events are fetched from DB without filters, then filtered in Python. This is required for context switch calculation, which needs all events to preserve temporal order and calculate accurate gaps between app switches.

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
