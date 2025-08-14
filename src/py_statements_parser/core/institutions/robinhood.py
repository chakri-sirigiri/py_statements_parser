"""Robinhood statement processor."""

from datetime import datetime
from pathlib import Path
from typing import Any

from .base import BaseInstitution


class RobinhoodInstitution(BaseInstitution):
    """Handles Robinhood statement processing."""

    def __init__(self, config: dict[str, Any], db_manager):
        """Initialize Robinhood institution handler."""
        super().__init__(config, db_manager)
        self.institution_name = "robinhood"

    def extract_statement_date(self, pdf_file: Path) -> datetime | None:
        """Extract the statement date from Robinhood statement."""
        self.logger.info("Robinhood statement processing not yet implemented")
        return None

    def extract_transactions(self, pdf_file: Path) -> list[dict[str, Any]]:
        """Extract transaction data from Robinhood statement."""
        self.logger.info("Robinhood statement processing not yet implemented")
        return []

    def generate_excel(self, transactions: list[dict[str, Any]], output_file: Path) -> None:
        """Generate Excel file with Robinhood transactions."""
        self.logger.info("Robinhood Excel generation not yet implemented")

    def enter_to_quicken(self, transactions: list[dict[str, Any]], quicken_config: Any) -> None:
        """Enter transactions into Quicken application."""
        self.logger.info("Robinhood Quicken integration not yet implemented")
