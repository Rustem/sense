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

## Prerequisites

**Grant Full Disk Access** to your Terminal application:
- Open **System Settings** → **Privacy & Security** → **Full Disk Access**
- Click **+** and add your terminal app (Terminal.app, iTerm, etc.)
- Restart your terminal

## Quick Start

```bash
# Install dependencies
uv sync

# Run dashboard (production mode - uses real KnowledgeC database)
SENSE_ENV=prod uv run uvicorn sense.api.main:app

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

# Sync the KnowledgeC database (for development mode)
./scripts/sync_db.sh

# Run tests
uv run pytest

# Run locally (dev environment - uses data/knowledgeC.db)
uv run uvicorn sense.api.main:app --reload

# Run with production database (uses ~/Library/Application Support/Knowledge/knowledgeC.db)
SENSE_ENV=prod uv run uvicorn sense.api.main:app --reload
```

## Requirements

- macOS with Full Disk Access
- Python 3.11+
- Access to `~/Library/Application Support/Knowledge/knowledgeC.db`

## Support

If you find Sense useful:
- ⭐ **Star this repo** to show your support
- ☕ **[Buy me a coffee](https://buymeacoffee.com/rkamun)** to fuel development

Your support helps keep this project maintained and improved!

## License

MIT
