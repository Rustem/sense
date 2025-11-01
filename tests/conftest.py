"""Pytest configuration and shared fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def sample_db_path() -> Path:
    """Path to sample KnowledgeC database for testing."""
    return Path(__file__).parent / "fixtures" / "test_knowledgeC.db"
