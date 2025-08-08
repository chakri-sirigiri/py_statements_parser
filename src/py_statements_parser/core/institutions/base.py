"""Base class for financial institution handlers."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from ..database import DatabaseManager


class BaseInstitution(ABC):
    """Base class for all financial institution handlers."""
    
    def __init__(self, config: Dict[str, Any], db_manager: DatabaseManager):
        """Initialize the institution handler."""
        self.config = config
        self.db_manager = db_manager
        self.logger = logger.bind(name=f"Institution.{self.__class__.__name__}")
    
    @abstractmethod
    def extract_statement_date(self, pdf_file: Path) -> Optional[datetime]:
        """Extract the statement date from a PDF file."""
        pass
    
    @abstractmethod
    def extract_transactions(self, pdf_file: Path) -> List[Dict[str, Any]]:
        """Extract transactions from a PDF statement."""
        pass
    
    @abstractmethod
    def generate_excel(self, transactions: List[Dict[str, Any]], output_file: Path) -> None:
        """Generate Excel file with extracted transactions."""
        pass
    
    @abstractmethod
    def enter_to_quicken(self, transactions: List[Dict[str, Any]], quicken_config: Any) -> None:
        """Enter transactions into Quicken application."""
        pass
    
    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Parse amount string to float, handling various formats."""
        if not amount_str or amount_str.strip() == "":
            return None
        
        # Remove common currency symbols and whitespace
        cleaned = amount_str.strip().replace("$", "").replace(",", "")
        
        # Handle negative amounts in parentheses
        if cleaned.startswith("(") and cleaned.endswith(")"):
            cleaned = "-" + cleaned[1:-1]
        
        # Handle negative amounts with minus sign
        if cleaned.startswith("-"):
            is_negative = True
            cleaned = cleaned[1:]
        else:
            is_negative = False
        
        try:
            amount = float(cleaned)
            return -amount if is_negative else amount
        except ValueError:
            self.logger.warning(f"Could not parse amount: {amount_str}")
            return None
    
    def _parse_date(self, date_str: str, formats: List[str] = None) -> Optional[datetime]:
        """Parse date string to datetime object."""
        if not date_str or date_str.strip() == "":
            return None
        
        if formats is None:
            formats = [
                "%m/%d/%Y",
                "%m-%d-%Y",
                "%Y-%m-%d",
                "%m/%d/%y",
                "%m-%d-%y",
                "%Y/%m/%d",
            ]
        
        cleaned = date_str.strip()
        
        for fmt in formats:
            try:
                return datetime.strptime(cleaned, fmt)
            except ValueError:
                continue
        
        self.logger.warning(f"Could not parse date: {date_str}")
        return None 