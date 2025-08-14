"""First Energy statement processor."""

from datetime import datetime
from pathlib import Path
from typing import Any

from .base import BaseInstitution


class FirstEnergyInstitution(BaseInstitution):
    """Handles First Energy statement processing."""

    def __init__(self, config: dict[str, Any], db_manager):
        """Initialize First Energy institution handler."""
        super().__init__(config, db_manager)
        self.institution_name = "first-energy"

    def extract_statement_date(self, pdf_file: Path) -> datetime | None:
        """Extract the statement date from First Energy statement."""
        self.logger.info("First Energy statement processing not yet implemented")
        return None

    def extract_transactions(self, pdf_file: Path) -> list[dict[str, Any]]:
        """Extract transaction data from First Energy statement."""
        self.logger.info("First Energy statement processing not yet implemented")
        return []

    def generate_excel(self, transactions: list[dict[str, Any]], output_file: Path) -> None:
        """Generate Excel file with First Energy transactions."""
        self.logger.info("First Energy Excel generation not yet implemented")

    def enter_to_quicken(self, transactions: list[dict[str, Any]], quicken_config: Any) -> None:
        """Enter transactions into Quicken application."""
        self.logger.info("First Energy Quicken integration not yet implemented")
