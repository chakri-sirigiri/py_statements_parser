"""Tests for the main CLI application."""

import pytest
from typer.testing import CliRunner
from src.py_statements_parser.main import app


@pytest.fixture
def runner():
    """Provide a CLI runner for testing."""
    return CliRunner()


def test_help_command(runner):
    """Test that help command works."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Process statements from various financial institutions" in result.output


def test_invalid_financial_institution(runner):
    """Test that invalid financial institution returns error."""
    result = runner.invoke(app, [
        "--financial-institution", "invalid",
        "--feature", "rename-file",
        "--statements-folder", "test"
    ])
    assert result.exit_code == 1
    assert "Invalid financial institution" in result.output


def test_invalid_feature(runner):
    """Test that invalid feature returns error."""
    result = runner.invoke(app, [
        "--financial-institution", "ipay",
        "--feature", "invalid-feature",
        "--statements-folder", "test"
    ])
    assert result.exit_code == 1
    assert "Invalid feature" in result.output


def test_missing_statements_folder(runner):
    """Test that missing statements folder returns error."""
    result = runner.invoke(app, [
        "--financial-institution", "ipay",
        "--feature", "rename-file"
    ])
    assert result.exit_code == 1
    assert "statements-folder is required" in result.output 