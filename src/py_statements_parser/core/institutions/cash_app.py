"""Cash App statement processor."""

from datetime import datetime
from pathlib import Path
from typing import Any

from .base import BaseInstitution


class CashAppInstitution(BaseInstitution):
    """Handles Cash App statement processing."""

    def __init__(self, config: dict[str, Any], db_manager):
        """Initialize Cash App institution handler."""
        super().__init__(config, db_manager)
        self.institution_name = "cash-app"

    def extract_statement_date(self, pdf_file: Path) -> datetime | None:
        """Extract the statement date from Cash App statement."""
        self.logger.info("Cash App statement processing not yet implemented")
        return None

    def extract_transactions(self, pdf_file: Path) -> list[dict[str, Any]]:
        """Extract transaction data from Cash App statement."""
        self.logger.info("Cash App statement processing not yet implemented")
        return []

    def generate_excel(self, transactions: list[dict[str, Any]], output_file: Path) -> None:
        """Generate Excel file with Cash App transactions."""
        self.logger.info("Cash App Excel generation not yet implemented")

    def enter_to_quicken(self, transactions: list[dict[str, Any]], quicken_config: Any) -> None:
        """Enter transactions into Quicken application."""
        self.logger.info("Cash App Quicken integration not yet implemented")
