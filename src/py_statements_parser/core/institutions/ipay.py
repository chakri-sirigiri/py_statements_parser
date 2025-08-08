"""ADP IPay statement processor."""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import fitz  # PyMuPDF
import pandas as pd
from loguru import logger

from .base import BaseInstitution


class IPayInstitution(BaseInstitution):
    """Handles ADP IPay statement processing."""
    
    def __init__(self, config: Dict[str, Any], db_manager):
        """Initialize IPay institution handler."""
        super().__init__(config, db_manager)
        self.institution_name = "ipay"
        
        # Define field patterns for IPay statements
        self.field_patterns = {
            "pay_date": r"Pay\s+Date[:\s]*(\d{1,2}/\d{1,2}/\d{4})",
            "pay_period": r"Pay\s+Period[:\s]*([^\\n]+)",
            "gross_pay": r"Gross\s+Pay[:\s]*([\d,]+\.?\d*)",
            "federal_income_tax": r"Federal\s+Income\s+Tax[:\s]*([-\d,]+\.?\d*)",
            "social_security_tax": r"Social\s+Security\s+Tax[:\s]*([-\d,]+\.?\d*)",
            "medicare_tax": r"Medicare\s+Tax[:\s]*([-\d,]+\.?\d*)",
            "oh_state_income_tax": r"OH\s+State\s+Income\s+Tax[:\s]*([-\d,]+\.?\d*)",
            "brooklyn_income_tax": r"Brooklyn\s+Income\s+Tax[:\s]*([-\d,]+\.?\d*)",
            "hsa_plan": r"HSA\s+Plan[:\s]*([-\d,]+\.?\d*)",
            "illness_plan": r"Illness\s+Plan\s+Lo[:\s]*([-\d,]+\.?\d*)",
            "legal": r"Legal[:\s]*([-\d,]+\.?\d*)",
            "life_insurance": r"Life\s+Ins[:\s]*([-\d,]+\.?\d*)",
            "pretax_dental": r"Pretax\s+Dental[:\s]*([-\d,]+\.?\d*)",
            "pretax_medical": r"Pretax\s+Medical[:\s]*([-\d,]+\.?\d*)",
            "pretax_vision": r"Pretax\s+Vision[:\s]*([-\d,]+\.?\d*)",
            "vol_acc_40_20": r"Vol\s+Acc\s+40/20[:\s]*([-\d,]+\.?\d*)",
            "vol_child_life": r"Vol\s+Child\s+Life[:\s]*([-\d,]+\.?\d*)",
            "vol_spousal_life": r"Vol\s+Spousl\s+Life[:\s]*([-\d,]+\.?\d*)",
            "k401_pretax": r"401K\s+Pretax[:\s]*([-\d,]+\.?\d*)",
            "net_pay": r"Net\s+Pay[:\s]*([\d,]+\.?\d*)",
        }
    
    def extract_statement_date(self, pdf_file: Path) -> Optional[datetime]:
        """Extract the pay date from IPay statement."""
        try:
            # Open PDF and extract text
            doc = fitz.open(pdf_file)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            
            # Look for pay date pattern
            pay_date_match = re.search(self.field_patterns["pay_date"], text, re.IGNORECASE)
            if pay_date_match:
                pay_date_str = pay_date_match.group(1)
                pay_date = self._parse_date(pay_date_str, ["%m/%d/%Y"])
                if pay_date:
                    self.logger.debug(f"Extracted pay date: {pay_date}")
                    return pay_date
            
            self.logger.warning(f"Could not extract pay date from {pdf_file.name}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting date from {pdf_file.name}: {str(e)}")
            return None
    
    def extract_transactions(self, pdf_file: Path) -> List[Dict[str, Any]]:
        """Extract transaction data from IPay statement."""
        try:
            # Open PDF and extract text
            doc = fitz.open(pdf_file)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            
            # Extract pay date first
            pay_date = self.extract_statement_date(pdf_file)
            if not pay_date:
                self.logger.error(f"Could not extract pay date from {pdf_file.name}")
                return []
            
            # Extract all fields
            transaction_data = {
                "institution": self.institution_name,
                "statement_date": pay_date.strftime("%Y-%m-%d"),
            }
            
            # Extract pay period
            pay_period_match = re.search(self.field_patterns["pay_period"], text, re.IGNORECASE)
            if pay_period_match:
                transaction_data["pay_period"] = pay_period_match.group(1).strip()
            
            # Extract all monetary fields
            for field_name, pattern in self.field_patterns.items():
                if field_name in ["pay_date", "pay_period"]:
                    continue
                
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    amount_str = match.group(1)
                    amount = self._parse_amount(amount_str)
                    if amount is not None:
                        # Map field names to database column names
                        db_field_name = self._map_field_name(field_name)
                        transaction_data[db_field_name] = amount
                        self.logger.debug(f"Extracted {field_name}: {amount}")
            
            # Validate that we have at least some data
            if len(transaction_data) < 3:  # institution, statement_date, and at least one field
                self.logger.warning(f"Insufficient data extracted from {pdf_file.name}")
                return []
            
            self.logger.info(f"Successfully extracted transaction data from {pdf_file.name}")
            return [transaction_data]
            
        except Exception as e:
            self.logger.error(f"Error extracting transactions from {pdf_file.name}: {str(e)}")
            return []
    
    def generate_excel(self, transactions: List[Dict[str, Any]], output_file: Path) -> None:
        """Generate Excel file with IPay transactions."""
        if not transactions:
            self.logger.warning("No transactions to export to Excel")
            return
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(transactions)
            
            # Reorder columns for better presentation
            column_order = [
                "statement_date",
                "pay_period",
                "gross_pay",
                "federal_income_tax",
                "social_security_tax",
                "medicare_tax",
                "state_income_tax",
                "local_income_tax",
                "hsa_plan",
                "illness_plan",
                "legal",
                "life_insurance",
                "pretax_dental",
                "pretax_medical",
                "pretax_vision",
                "vol_acc_40_20",
                "vol_child_life",
                "vol_spousal_life",
                "k401_pretax",
                "net_pay",
            ]
            
            # Filter to only include columns that exist in the data
            available_columns = [col for col in column_order if col in df.columns]
            df = df[available_columns]
            
            # Write to Excel
            with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="IPay Transactions", index=False)
                
                # Get the worksheet to format it
                worksheet = writer.sheets["IPay Transactions"]
                
                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            self.logger.info(f"Generated Excel file: {output_file}")
            
        except Exception as e:
            self.logger.error(f"Error generating Excel file: {str(e)}")
            raise
    
    def enter_to_quicken(self, transactions: List[Dict[str, Any]], quicken_config: Any) -> None:
        """Enter transactions into Quicken application."""
        # This is a placeholder implementation
        # In a real implementation, this would use Quicken's API or automation
        self.logger.info("Quicken integration not yet implemented")
        self.logger.info(f"Would enter {len(transactions)} transactions into Quicken")
    
    def _map_field_name(self, field_name: str) -> str:
        """Map field names from pattern names to database column names."""
        field_mapping = {
            "oh_state_income_tax": "state_income_tax",
            "brooklyn_income_tax": "local_income_tax",
            "illness_plan": "illness_plan",
            "life_insurance": "life_insurance",
            "vol_acc_40_20": "vol_acc_40_20",
            "vol_child_life": "vol_child_life",
            "vol_spousal_life": "vol_spousal_life",
            "k401_pretax": "k401_pretax",
        }
        
        return field_mapping.get(field_name, field_name) 