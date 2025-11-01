# Sense

macOS activity tracker using KnowledgeC database. Track focus time, context switches, and usage patterns.

## Features

- **Focus Time Analysis** - Your uninterrupted usage sessions per app
- **Context Switch Tracking** - Identification of frequent app switching patterns
- **Daily/Weekly Metrics** - Usage breakdowns and trends
- **Web Dashboard** - Local-first visualization
- **MCP Server** - Query stats via Claude

## Quick Start

```bash
# Install dependencies
uv sync

# Run dashboard
uv run sense serve

# Open browser
open http://localhost:8000
```

## API

```bash
# Get daily stats
curl http://localhost:8000/api/stats/daily?date=2024-10-31

# Get weekly summary
curl http://localhost:8000/api/stats/weekly

# Top context switches
curl http://localhost:8000/api/switches/top?limit=10
```

## Tech Stack

- **Backend:** FastAPI + SQLite (KnowledgeC)
- **Cache:** In-memory (dict with TTL)
- **Frontend:** Jinja2 templates
- **Packaging:** uv + pyproject.toml

## Privacy

- All data stays local
- Read-only access to KnowledgeC
- No external services

## Development

```bash
# Install dev dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Run locally
uv run uvicorn sense.api.main:app --reload
```

## Requirements

- macOS with Full Disk Access
- Python 3.11+
- Access to `~/Library/Application Support/Knowledge/knowledgeC.db`

## License

MIT
