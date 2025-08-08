"""Pytest configuration and shared fixtures."""

import pytest
from pathlib import Path
from src.py_statements_parser.core.config import Config


@pytest.fixture
def sample_config():
    """Provide a sample configuration for testing."""
    return Config(
        database={
            "type": "sqlite",
            "path": ":memory:"
        },
        logging={
            "level": "DEBUG",
            "file": None
        }
    )


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for testing."""
    return tmp_path


@pytest.fixture
def sample_pdf_path(temp_dir):
    """Provide a path for a sample PDF file."""
    return temp_dir / "sample_statement.pdf" 