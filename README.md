# Sense

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

macOS activity tracker using KnowledgeC database. Track focus time, context switches, and usage patterns.

## Features

- **Focus Time Analysis** - Your uninterrupted usage sessions per app
- **Context Switch Tracking** - Identification of frequent app switching patterns
- **Daily/Weekly Metrics** - Usage breakdowns and trends
- **Web Dashboard** - Local-first visualization
- **MCP Server** - Query stats via Claude

## Screenshots

![Daily overview with focus apps and interruption patterns](images/Dashboard%20top%20page.png)
*Daily metrics, insights, and top focus apps with interruption patterns*

![Context switch timeline showing app transitions](images/Dashboard%20context%20switches.png)
*Detailed context switch timeline with timestamp and app transitions*

![Hourly context switching activity and app timeline](images/Dashboard%20bottom.png)
*Hourly context switching trends and visual timeline of app usage*

## Prerequisites

1. **Grant Full Disk Access** to your Terminal application:
   - Open **System Settings** → **Privacy & Security** → **Full Disk Access**
   - Click **+** and add your terminal app (Terminal.app, iTerm, etc.)
   - Restart your terminal

2. **Sync the KnowledgeC database**:
   ```bash
   ./scripts/sync_db.sh
   ```
   This copies the database to avoid permission issues during development.

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
