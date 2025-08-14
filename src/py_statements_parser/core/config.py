"""Configuration management for Py Statements Parser."""

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


def load_env_file(env_file_path: Path) -> None:
    """Load environment variables from .env file."""
    if env_file_path.exists():
        with open(env_file_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()


class DatabaseConfig(BaseModel):
    """Database configuration settings."""

    type: str = Field(default="sqlite", description="Database type (sqlite, postgresql, mysql)")
    path: str | None = Field(default=None, description="Database file path for SQLite")
    host: str | None = Field(default=None, description="Database host")
    port: int | None = Field(default=None, description="Database port")
    name: str | None = Field(default=None, description="Database name")
    username: str | None = Field(default=None, description="Database username")
    password: str | None = Field(default=None, description="Database password")


class LoggingConfig(BaseModel):
    """Logging configuration settings."""

    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}", description="Log format"
    )
    file: str | None = Field(default="app.log", description="Log file path")
    rotation: str = Field(default="10 MB", description="Log rotation size")
    retention: str = Field(default="30 days", description="Log retention period")


class QuickenConfig(BaseModel):
    """Quicken application configuration."""

    enabled: bool = Field(default=False, description="Enable Quicken integration")
    executable_path: str | None = Field(default=None, description="Quicken executable path")
    data_file: str | None = Field(default=None, description="Quicken data file path")


class Config(BaseModel):
    """Main configuration class."""

    database: DatabaseConfig = Field(default_factory=DatabaseConfig, description="Database configuration")
    logging: LoggingConfig = Field(default_factory=LoggingConfig, description="Logging configuration")
    quicken: QuickenConfig = Field(default_factory=QuickenConfig, description="Quicken configuration")

    # Input folder for unsorted statements (from INPUT_STATEMENTS_FOLDER env var)
    input_statements_folder: str | None = Field(
        default=None, description="Input folder containing unsorted statements (from INPUT_STATEMENTS_FOLDER env var)"
    )

    # Target folder for organized statements (from TARGET_STATEMENTS_FOLDER env var)
    target_statements_folder: str | None = Field(
        default=None, description="Target folder for organized statements (from TARGET_STATEMENTS_FOLDER env var)"
    )

    # Financial institution specific settings
    institutions: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="Institution-specific configuration"
    )

    def __init__(self, **data):
        """Initialize configuration with environment variable support."""
        # Load .env file if it exists
        env_file = Path(".env")
        if env_file.exists():
            load_env_file(env_file)

        super().__init__(**data)

        # Get input and target statements folders from environment variables
        if not self.input_statements_folder:
            self.input_statements_folder = os.getenv("INPUT_STATEMENTS_FOLDER")

        if not self.target_statements_folder:
            self.target_statements_folder = os.getenv("TARGET_STATEMENTS_FOLDER")

    @classmethod
    def from_file(cls, config_path: Path) -> "Config":
        """Load configuration from YAML file."""
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        return cls(**config_data)

    def save_to_file(self, config_path: Path) -> None:
        """Save configuration to YAML file."""
        config_data = self.model_dump()

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, default_flow_style=False, indent=2)

    def get_institution_config(self, institution: str) -> dict[str, Any]:
        """Get institution-specific configuration."""
        return self.institutions.get(institution, {})

    def get_target_folder(self, institution: str, year: int) -> Path:
        """Get the target folder path for a specific institution and year."""
        if not self.target_statements_folder:
            raise ValueError("TARGET_STATEMENTS_FOLDER environment variable not set")

        target_path = Path(self.target_statements_folder).expanduser() / institution / str(year)
        target_path.mkdir(parents=True, exist_ok=True)
        return target_path
