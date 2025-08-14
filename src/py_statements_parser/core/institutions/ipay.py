"""ADP IPay statement processor."""

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import pdfplumber

from .base import BaseInstitution


class IPayInstitution(BaseInstitution):
    """Handles ADP IPay statement processing."""

    def __init__(self, config: dict[str, Any], db_manager):
        """Initialize IPay institution handler."""
        super().__init__(config, db_manager)
        self.institution_name = "ipay"

        # Define field patterns for IPay statements
        self.field_patterns = {
            "pay_date": r"Pay\s+Date[:\s]*(\d{1,2}/\d{1,2}/\d{4})",
            "regular_pay": r"Regular[:\s]*([\d,]+\.?\d*)",
            "bonus": r"Bonus[:\s]*([\d,]+\.?\d*)",
            "performance": r"Performance[:\s]*([\d,]+\.?\d*)",
            "vacation": r"Vacation[:\s]*([\d,]+\.?\d*)",
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
            "vol_acc_40_20": r"Vol\s+Acc\s+(?:40/20|20/10)[:\s]*([-\d,]+\.?\d*)",
            "vol_child_life": r"Vol\s+Child\s+Life[:\s]*([-\d,]+\.?\d*)",
            "vol_spousal_life": r"Vol\s+Spousl\s+Life[:\s]*([-\d,]+\.?\d*)",
            "k401_pretax": r"401K\s+Pretax[:\s]*([-\d,]+\.?\d*)",
            "espp": r"Espp[:\s]*([-\d,]+\.?\d*)",
            "k401_loan_gp1": r"401K\s+Loan\s+Gp1[:\s]*([-\d,]+\.?\d*)",
            "net_pay": r"Net\s+Pay[:\s]*([\d,]+\.?\d*)",
        }

    def extract_statement_date(self, pdf_file: Path) -> datetime | None:
        """Extract the pay date from IPay statement."""
        try:
            # Open PDF and extract text using pdfplumber
            with pdfplumber.open(pdf_file) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)

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

    def _is_bonus_paycheck(self, text: str, filename: str = "") -> bool:
        """Determine if this is a bonus paycheck by looking for the bonus pattern in filename and content."""
        # First check the filename - if it contains 'bonus', treat as bonus paycheck
        if filename and "bonus" in filename.lower():
            self.logger.debug(f"Filename contains 'bonus': {filename}")
            return True

        # Then check the PDF content for bonus patterns
        lines = text.splitlines()
        for line in lines:
            if "bonus" in line.lower():
                import re

                bonus_matches = re.findall(r"(\d+ \d+ \d+)", line)
                if len(bonus_matches) >= 2 and bonus_matches[0] == bonus_matches[1]:
                    self.logger.debug(f"PDF content contains bonus pattern: {line}")
                    return True
        return False

    def _is_vacation_paycheck(self, text: str, filename: str = "") -> bool:
        """Determine if this is a vacation paycheck by looking for the vacation pattern in filename and content."""
        # First check the filename - if it contains 'vacation', treat as vacation paycheck
        if filename and "vacation" in filename.lower():
            self.logger.debug(f"Filename contains 'vacation': {filename}")
            return True

        # Then check the PDF content for vacation patterns
        lines = text.splitlines()
        for line in lines:
            if "vacation" in line.lower():
                import re

                vacation_matches = re.findall(r"(\d+ \d+ \d+)", line)
                if len(vacation_matches) >= 2 and vacation_matches[0] == vacation_matches[1]:
                    self.logger.debug(f"PDF content contains vacation pattern: {line}")
                    return True
        return False

    def extract_transactions(self, pdf_file: Path) -> list[dict[str, Any]]:
        """Extract transaction data from IPay statement using improved extraction logic."""
        try:
            # Open PDF and extract text using pdfplumber
            with pdfplumber.open(pdf_file) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)

            # Debug: Show the full extracted text
            self.logger.debug(f"Full PDF text from {pdf_file.name}:")
            self.logger.debug("=" * 80)
            self.logger.debug(text)
            self.logger.debug("=" * 80)

            # Extract pay date first
            pay_date = self.extract_statement_date(pdf_file)
            if not pay_date:
                self.logger.error(f"Could not extract pay date from {pdf_file.name}")
                return []

            # Determine paycheck type
            is_bonus_paycheck = self._is_bonus_paycheck(text, pdf_file.name)
            is_vacation_paycheck = self._is_vacation_paycheck(text, pdf_file.name)

            if is_bonus_paycheck:
                paycheck_type = "bonus"
            elif is_vacation_paycheck:
                paycheck_type = "vacation"
            else:
                paycheck_type = "regular"

            self.logger.debug(f"Paycheck type for {pdf_file.name}: {paycheck_type}")

            # Initialize transaction data
            transaction_data = {
                "institution": self.institution_name,
                "statement_date": pay_date.strftime("%Y-%m-%d"),
                "source_file": pdf_file.name,
            }

            # Process text line by line for better extraction
            lines = text.splitlines()
            self.logger.debug(f"Processing {len(lines)} lines from PDF")

            for i, line in enumerate(lines):
                # Debug: Log lines that might contain relevant data
                if any(
                    keyword in line.lower()
                    for keyword in ["regular", "bonus", "gross", "tax", "deduction", "net", "pay"]
                ):
                    self.logger.debug(f"Processing line {i}: '{line}'")

                self._extract_regular_pay(line, i, transaction_data, is_bonus_paycheck, is_vacation_paycheck)
                self._extract_other_income(line, i, transaction_data, is_bonus_paycheck, is_vacation_paycheck)
                # Extract bonus/performance for bonus paychecks, vacation for vacation paychecks
                if is_bonus_paycheck:
                    self._extract_bonus(line, i, transaction_data)
                elif is_vacation_paycheck:
                    self._extract_vacation(line, i, transaction_data)
                self._extract_gross_pay(line, i, transaction_data)
                self._extract_taxes(line, i, transaction_data)
                # Extract deductions based on paycheck type
                if is_bonus_paycheck:
                    # For bonus paychecks, extract ESPP and 401K pretax if present
                    self._extract_bonus_deductions(line, i, transaction_data)
                elif is_vacation_paycheck:
                    # For vacation paychecks, extract only statutory deductions and 401K pretax
                    self._extract_vacation_deductions(line, i, transaction_data)
                else:
                    # For regular paychecks, extract all deductions
                    self._extract_deductions(line, i, transaction_data)
                self._extract_net_pay(line, i, transaction_data)

                # Note: Checking account extraction is now handled in the main post-processing section
                # when net pay is exactly $0.00

            # Note: Gross pay is extracted directly from PDF, not calculated
            # For bonus and vacation paychecks, log that other income was skipped
            if is_bonus_paycheck:
                self.logger.debug("Bonus paycheck: other income extraction skipped (YTD values only)")
            elif is_vacation_paycheck:
                self.logger.debug("Vacation paycheck: other income extraction skipped (YTD values only)")

            # Net Pay Logic:
            # 1. If net pay has a value (current pay period) - use that
            # 2. If net pay is $0 or missing - sum up all Checking* accounts (first amount only)
            net_pay = transaction_data.get("net_pay")

            if net_pay and net_pay != "0.00":
                # Net pay has a value - use it
                self.logger.debug(f"Net pay has value: {net_pay} - using extracted value")
            else:
                # Net pay is $0 or missing - calculate from checking accounts
                self.logger.debug("Net pay is $0 or missing, calculating from checking accounts")
                total_checking_amount = 0.0
                checking_accounts_found = []

                # Scan all lines for checking accounts and sum up current period amounts
                for i, line in enumerate(lines):
                    if "checking" in line.lower():
                        self.logger.debug(f"Found checking account line {i}: '{line}'")
                        # Extract amounts using a more sophisticated approach
                        # Try different patterns to handle both 2-number and 3-number formats
                        checking_matches = []

                        # Check if the line contains 3-number amounts (e.g., "2 585 90")
                        # Look for patterns like "2 585 90" (thousands format) after "checking"
                        # This is more specific than just any 3 digits
                        # First check if it looks like two 2-number amounts (e.g., "221 16 221 16")
                        # Pattern: exactly 4 digits with spaces (2+2 format)
                        has_two_2num_amounts = re.search(r"\bchecking\d*\s+\d+\s+\d+\s+\d+\s+\d+$", line.lower())

                        if has_two_2num_amounts:
                            # This is two 2-number amounts, use 2-number pattern
                            has_3num_format = False
                        else:
                            # Check for 3-number format
                            has_3num_format = re.search(r"\bchecking\d*\s+\d+\s+\d+\s+\d+", line.lower())

                        if has_3num_format:
                            # Use 3-number pattern (e.g., "2 585 90")
                            pattern_3num = r"\bchecking\d*\s+(\d+\s+\d+\s+\d+)(?:\s+(\d+\s+\d+\s+\d+))?"
                            checking_matches = re.findall(pattern_3num, line.lower())
                        else:
                            # Use 2-number pattern (e.g., "221 16")
                            pattern_2num = r"\bchecking\d*\s+(\d+\s+\d+)(?:\s+(\d+\s+\d+))?"
                            checking_matches = re.findall(pattern_2num, line.lower())
                        if checking_matches:
                            for match in checking_matches:
                                if len(match) == 2 and match[1]:
                                    # Two values found: first is current period, second is YTD
                                    amount_str = match[0].replace(" ", "")
                                    ytd_amount_str = match[1].replace(" ", "")
                                    self.logger.debug(
                                        f"Two amounts found, using first (current period): {match[0]} (ignoring YTD: {match[1]})"
                                    )

                                    if len(amount_str) >= 3:
                                        dollars = amount_str[:-2]
                                        cents = amount_str[-2:]
                                        amount = float(f"{dollars}.{cents}")
                                        total_checking_amount += amount
                                        checking_accounts_found.append(amount)
                                        self.logger.debug(f"Extracted checking amount (current period): {amount}")
                                else:
                                    # Only one value found: this is YTD only, current period = $0
                                    ytd_amount_str = match[0].replace(" ", "")
                                    self.logger.debug(
                                        f"One amount found (YTD only): {match[0]} - current period amount = $0.00"
                                    )

                                    # Current period amount is $0, so don't add anything to total
                                    # But we could log the YTD amount for reference
                                    if len(ytd_amount_str) >= 3:
                                        ytd_dollars = ytd_amount_str[:-2]
                                        ytd_cents = ytd_amount_str[-2:]
                                        ytd_amount = float(f"{ytd_dollars}.{ytd_cents}")
                                        self.logger.debug(
                                            f"YTD amount: ${ytd_amount:.2f} (not added to current period total)"
                                        )

                # Set net pay to sum of all checking accounts (current period only)
                if total_checking_amount > 0:
                    transaction_data["net_pay"] = f"{total_checking_amount:.2f}"
                    self.logger.debug(
                        f"Calculated Net Pay from {len(checking_accounts_found)} checking accounts: {total_checking_amount} (accounts: {checking_accounts_found})"
                    )
                else:
                    self.logger.debug("No valid checking account amounts found, keeping net pay as $0.00")

            # Debug: Show what was extracted
            self.logger.debug(f"Extracted data: {transaction_data}")

            # Validate that we have at least some data
            if len(transaction_data) < 3:  # institution, statement_date, and at least one field
                self.logger.warning(
                    f"Insufficient data extracted from {pdf_file.name}. Only found: {list(transaction_data.keys())}"
                )
                return []

            # Validate paycheck calculations - log errors but continue processing
            try:
                self._validate_paycheck_calculations(transaction_data, is_bonus_paycheck, is_vacation_paycheck)
                self.logger.info(f"Paycheck validation PASSED for {pdf_file.name}")
            except ValueError as e:
                # Log the validation error but continue processing to insert into table
                self.logger.error(f"Paycheck validation FAILED for {pdf_file.name}: {str(e)}")
                self.logger.warning(
                    f"Continuing to insert transaction into table despite validation failure for {pdf_file.name}"
                )

            self.logger.info(f"Successfully extracted and validated transaction data from {pdf_file.name}")
            return [transaction_data]

        except Exception as e:
            self.logger.error(f"Error extracting transactions from {pdf_file.name}: {str(e)}")
            return []

    def generate_excel(self, transactions: list[dict[str, Any]], output_file: Path) -> None:
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
                "regular_pay",
                "bonus",
                "other_income",
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
                "dep_care",
                "vol_acc_40_20",
                "vol_child_life",
                "vol_spousal_life",
                "k401_pretax",
                "espp",
                "k401_loan_gp1",
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
                        except Exception:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width

            self.logger.info(f"Generated Excel file: {output_file}")

        except Exception as e:
            self.logger.error(f"Error generating Excel file: {str(e)}")
            raise

    def enter_to_quicken(self, transactions: list[dict[str, Any]], quicken_config: Any) -> None:
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
            "hsa_plan": "hsa_plan",
            "illness_plan": "illness_plan",
            "life_insurance": "life_insurance",
            "vol_acc_40_20": "vol_acc_40_20",
            "vol_child_life": "vol_child_life",
            "vol_spousal_life": "vol_spousal_life",
            "k401_pretax": "k401_pretax",
            "regular_pay": "regular_pay",
            "bonus": "bonus",
        }

        return field_mapping.get(field_name, field_name)

    def _convert_pdf_number(self, num_str: str) -> str:
        """
        Convert PDF number format to standard decimal format.
        Converts '1 218 00' -> '1218.00', '5 307 50' -> '5307.50'
        """
        parts = num_str.strip().split()
        if len(parts) >= 2 and all(p.isdigit() for p in parts):
            integer_part = "".join(parts[:-1])
            cents = parts[-1]
            return f"{integer_part}.{cents}"
        return num_str.replace(" ", "")

    def _extract_regular_pay(
        self,
        line: str,
        line_num: int,
        row: dict[str, Any],
        is_bonus_paycheck: bool = False,
        is_vacation_paycheck: bool = False,
    ) -> None:
        """Extract regular pay from line."""
        if "regular" in line.lower():
            self.logger.debug(f"Found 'regular' in line {line_num}: '{line}'")

            # If this is a bonus or vacation paycheck, skip regular pay extraction (it's YTD, not current period)
            if is_bonus_paycheck:
                self.logger.debug("Bonus paycheck detected, skipping regular pay extraction (YTD value)")
                return
            if is_vacation_paycheck:
                self.logger.debug("Vacation paycheck detected, skipping regular pay extraction (YTD value)")
                return

            # Extract all number patterns from the line
            # Format: "Regular 1060 42 1 060 42 1 060 42 Your federal taxable wages this period are"
            # Pattern: number space number (like "1060 42")
            matches = re.findall(r"(\d+ \d+)", line)
            self.logger.debug(f"Regular pay matches: {matches}")

            if len(matches) >= 2:
                # Two values found: first is current period, second is YTD
                current_period_value = self._convert_pdf_number(matches[0])
                ytd_value = self._convert_pdf_number(matches[1])
                row["regular_pay"] = current_period_value
                self.logger.debug(
                    f"Extracted Regular Pay (current period) from line {line_num}: {current_period_value} (YTD: {ytd_value})"
                )
            elif len(matches) == 1:
                # Only one value found: assume it's YTD only, skip extraction
                ytd_value = self._convert_pdf_number(matches[0])
                self.logger.debug(f"Regular Pay YTD only found in line {line_num}: {ytd_value} - skipping extraction")
            else:
                self.logger.debug(f"No regular pay pattern match found in line {line_num}")

    def _extract_other_income(
        self,
        line: str,
        line_num: int,
        row: dict[str, Any],
        is_bonus_paycheck: bool = False,
        is_vacation_paycheck: bool = False,
    ) -> None:
        """Extract other income from line (Cola, Retro Cola, Contribution, etc.)."""
        # If this is a bonus or vacation paycheck, skip other income extraction (it's YTD, not current period)
        if is_bonus_paycheck:
            self.logger.debug("Bonus paycheck detected, skipping other income extraction (YTD values)")
            return
        if is_vacation_paycheck:
            self.logger.debug("Vacation paycheck detected, skipping other income extraction (YTD values)")
            return

        # Define other income patterns
        other_income_patterns = [
            "cola",
            "retro cola",
            "contribution",
            "retro contribution",
            "retro contribtn",
            "award",
            "skillpay allow",
        ]

        line_lower = line.lower()
        for pattern in other_income_patterns:
            if pattern in line_lower:
                self.logger.debug(f"Found other income pattern '{pattern}' in line {line_num}: '{line}'")

                # Extract amounts using a more precise approach
                # Look for the main amount patterns right after the income type keyword
                # This avoids capturing additional text that looks like amounts

                # Find the position of the income type keyword
                keyword_pos = line.lower().find(pattern)
                if keyword_pos == -1:
                    continue

                # Get the text after the keyword
                text_after_keyword = line[keyword_pos + len(pattern) :].strip()

                # Look for the first two main amounts in sequence
                # These should be the current period and YTD amounts
                # Use more specific patterns to avoid capturing partial amounts

                # First, try to find a two-number amount (e.g., "125 00") - this is more common
                first_amount_match = re.search(r"^(\d+\s+\d+)", text_after_keyword)
                if first_amount_match:
                    first_amount = first_amount_match.group(1)
                    # Look for second amount after the first one
                    remaining_text = text_after_keyword[first_amount_match.end() :].strip()
                    # Try to find a three-number amount first (e.g., "1 000 00")
                    second_amount_match = re.search(r"^(\d+\s+\d+\s+\d+)", remaining_text)
                    if second_amount_match:
                        second_amount = second_amount_match.group(1)
                        matches = [first_amount, second_amount]
                    else:
                        # Try two-number pattern for second amount
                        second_amount_match = re.search(r"^(\d+\s+\d+)", remaining_text)
                        if second_amount_match:
                            second_amount = second_amount_match.group(1)
                            matches = [first_amount, second_amount]
                        else:
                            matches = [first_amount]
                else:
                    # Try three-number pattern (e.g., "1 625 00")
                    first_amount_match = re.search(r"^(\d+\s+\d+\s+\d+)", text_after_keyword)
                    if first_amount_match:
                        first_amount = first_amount_match.group(1)
                        # Look for second amount after the first one
                        remaining_text = text_after_keyword[first_amount_match.end() :].strip()
                        second_amount_match = re.search(r"^(\d+\s+\d+\s+\d+)", remaining_text)
                        if second_amount_match:
                            second_amount = second_amount_match.group(1)
                            matches = [first_amount, second_amount]
                        else:
                            # Try two-number pattern for second amount
                            second_amount_match = re.search(r"^(\d+\s+\d+)", remaining_text)
                            if second_amount_match:
                                second_amount = second_amount_match.group(1)
                                matches = [first_amount, second_amount]
                            else:
                                matches = [first_amount]
                    else:
                        matches = []

                self.logger.debug(f"Other income matches for {pattern}: {matches}")

                if len(matches) >= 2:
                    # Two values found: first is current period, second is YTD
                    current_period_value = self._convert_pdf_number(matches[0])
                    ytd_value = self._convert_pdf_number(matches[1])

                    # Add to existing other_income if it exists
                    existing_other_income = row.get("other_income", 0)
                    if isinstance(existing_other_income, str):
                        existing_other_income = float(existing_other_income)
                    new_total = existing_other_income + float(current_period_value)
                    row["other_income"] = f"{new_total:.2f}"

                    self.logger.debug(
                        f"Extracted Other Income ({pattern}) from line {line_num}: {current_period_value} (YTD: {ytd_value}), total: {row['other_income']}"
                    )
                    break
                elif len(matches) == 1:
                    # Only one value found: check if it's followed by special characters or notes
                    # If it's just a clean amount, treat as YTD only
                    # If it's followed by special chars/notes, treat as current period
                    single_amount = matches[0]
                    amount_end_pos = line.lower().find(single_amount) + len(single_amount)
                    remaining_after_amount = line[amount_end_pos:].strip()

                    # For single amounts, be very conservative - default to YTD unless there are very clear current period indicators
                    # Only treat as current period if it has specific currency symbols or tax-related flags
                    meaningful_content = False
                    if remaining_after_amount:
                        # Check if it starts with technical details that should be ignored
                        if not remaining_after_amount.lower().startswith(("g t l", "checking")):
                            # For single amounts, only treat as current period if it has very specific indicators
                            # like currency symbols ($) or specific exclusion flags
                            # Note: Standard paycheck text like "federal taxable wages this period" is NOT an indicator
                            # Note: Asterisk (*) in paycheck formatting is NOT an indicator
                            # Note: "excluded from federal taxable wages" is standard text, not an indicator
                            if any(char in remaining_after_amount for char in ["$"]) or any(
                                term in remaining_after_amount.lower() for term in ["non-taxable"]
                            ):
                                meaningful_content = True

                    if meaningful_content:
                        # Has meaningful content (like $, *, or notes) - treat as current period
                        current_period_value = self._convert_pdf_number(single_amount)
                        existing_other_income = row.get("other_income", 0)
                        if isinstance(existing_other_income, str):
                            existing_other_income = float(existing_other_income)
                        new_total = existing_other_income + float(current_period_value)
                        row["other_income"] = f"{new_total:.2f}"
                        self.logger.debug(
                            f"Other Income ({pattern}) single amount with meaningful notes found in line {line_num}: {current_period_value} - treating as current period"
                        )
                    else:
                        # Clean single amount or technical details - treat as YTD only, skip extraction
                        ytd_value = self._convert_pdf_number(single_amount)
                        self.logger.debug(
                            f"Other Income ({pattern}) YTD only found in line {line_num}: {ytd_value} - skipping extraction"
                        )
                    break

    def _extract_bonus(self, line: str, line_num: int, row: dict[str, Any]) -> None:
        """Extract bonus or performance from line."""
        line_lower = line.lower()
        if "bonus" in line_lower or "performance" in line_lower:
            bonus_type = "bonus" if "bonus" in line_lower else "performance"
            self.logger.debug(f"Found '{bonus_type}' in line {line_num}: '{line}'")

            # Check if line contains $ sign - if so, second amount might be from different line item
            has_dollar_sign = "$" in line

            # Use more specific pattern to extract amounts that are clearly part of the bonus line
            # Look for bonus/performance followed by amount(s)
            specific_matches = re.findall(rf"{bonus_type}\s+(\d+ \d+ \d+)(?:\s+(\d+ \d+ \d+))?", line_lower)
            self.logger.debug(f"{bonus_type.capitalize()} specific matches: {specific_matches}")

            if specific_matches and specific_matches[0]:
                if len(specific_matches[0]) == 2 and specific_matches[0][1] and not has_dollar_sign:
                    # Two values found and no $ sign: first is current period, second is YTD
                    current_period_value = self._convert_pdf_number(specific_matches[0][0])
                    ytd_value = self._convert_pdf_number(specific_matches[0][1])
                    row["bonus"] = current_period_value
                    self.logger.debug(
                        f"Extracted {bonus_type.capitalize()} (current period) from line {line_num}: {current_period_value} (YTD: {ytd_value})"
                    )
                else:
                    # Only one value found or $ sign present: treat as current period only
                    current_period_value = self._convert_pdf_number(specific_matches[0][0])
                    row["bonus"] = current_period_value
                    if has_dollar_sign:
                        self.logger.debug(
                            f"Extracted {bonus_type.capitalize()} (current period) from line {line_num}: {current_period_value} (ignoring second amount due to $ sign)"
                        )
                    else:
                        self.logger.debug(
                            f"Extracted {bonus_type.capitalize()} (current period) from line {line_num}: {current_period_value}"
                        )
            else:
                self.logger.debug(f"No {bonus_type} pattern match found in line {line_num}")

    def _extract_vacation(self, line: str, line_num: int, row: dict[str, Any]) -> None:
        """Extract vacation pay from line and map to other_income."""
        line_lower = line.lower()
        if "vacation" in line_lower:
            self.logger.debug(f"Found 'vacation' in line {line_num}: '{line}'")

            # Check if line contains $ sign - if so, second amount might be from different line item
            has_dollar_sign = "$" in line

            # Use more specific pattern to extract amounts that are clearly part of the vacation line
            # Look for vacation followed by amount(s) - more flexible pattern
            specific_matches = re.findall(r"vacation[:\s-]*(\d+ \d+ \d+)(?:\s+(\d+ \d+ \d+))?", line_lower)
            self.logger.debug(f"Vacation specific matches: {specific_matches}")

            if specific_matches and specific_matches[0]:
                if len(specific_matches[0]) == 2 and specific_matches[0][1] and not has_dollar_sign:
                    # Two values found and no $ sign: first is current period, second is YTD
                    current_period_value = self._convert_pdf_number(specific_matches[0][0])
                    ytd_value = self._convert_pdf_number(specific_matches[0][1])
                    row["other_income"] = current_period_value
                    self.logger.debug(
                        f"Extracted Vacation (current period) from line {line_num}: {current_period_value} (YTD: {ytd_value}) - mapped to other_income"
                    )
                else:
                    # Only one value found or $ sign present: treat as current period only
                    current_period_value = self._convert_pdf_number(specific_matches[0][0])
                    row["other_income"] = current_period_value
                    if has_dollar_sign:
                        self.logger.debug(
                            f"Extracted Vacation (current period) from line {line_num}: {current_period_value} (ignoring second amount due to $ sign) - mapped to other_income"
                        )
                    else:
                        self.logger.debug(
                            f"Extracted Vacation (current period) from line {line_num}: {current_period_value} - mapped to other_income"
                        )
            else:
                self.logger.debug(f"No vacation pattern match found in line {line_num}")

    def _extract_gross_pay(self, line: str, line_num: int, row: dict[str, Any]) -> None:
        """Extract gross pay from line."""
        if "gross pay" in line.lower():
            self.logger.debug(f"Found 'gross pay' in line {line_num}: '{line}'")

            # Look for two-value pattern: current period + YTD
            # Pattern: "Gross Pay 1 218 00 1 218 00" (current period + YTD)
            matches = re.findall(r"(\d+ \d+ \d+)", line)
            self.logger.debug(f"Gross pay matches: {matches}")

            if len(matches) >= 2:
                # Two values found: first is current period, second is YTD
                current_period_value = self._convert_pdf_number(matches[0])
                ytd_value = self._convert_pdf_number(matches[1])
                row["gross_pay"] = current_period_value
                self.logger.debug(
                    f"Extracted Gross Pay (current period) from line {line_num}: {current_period_value} (YTD: {ytd_value})"
                )
            elif len(matches) == 1:
                # Only one value found: assume it's YTD only, skip extraction
                ytd_value = self._convert_pdf_number(matches[0])
                self.logger.debug(f"Gross Pay YTD only found in line {line_num}: {ytd_value} - skipping extraction")
            else:
                self.logger.debug(f"No gross pay pattern match found in line {line_num}")

    def _extract_taxes(self, line: str, line_num: int, row: dict[str, Any]) -> None:
        """Extract tax information from line."""
        tax_patterns = {
            "federal income tax": "federal_income_tax",
            "social security tax": "social_security_tax",
            "medicare tax": "medicare_tax",
            "oh state income tax": "state_income_tax",
            "nc state income tax": "state_income_tax",
            "brooklyn income tax": "local_income_tax",
            "cleveland income tax": "local_income_tax",
        }

        for pattern, field_name in tax_patterns.items():
            if pattern in line.lower():
                self.logger.debug(f"Found tax pattern '{pattern}' in line {line_num}: '{line}'")
                matches = re.findall(r"(-?\d{1,3}(?: \d{3})* \d{2})", line)
                self.logger.debug(f"Tax matches for {field_name}: {matches}")

                if len(matches) >= 2:
                    # Two values found: first is current period, second is YTD
                    current_period_value = matches[0]
                    ytd_value = matches[1]
                    value = current_period_value.lstrip("-")  # Remove any negative sign
                    tax_value = self._convert_pdf_number(value)
                    row[field_name] = tax_value
                    self.logger.debug(
                        f"Extracted {field_name} (current period) from line {line_num}: {tax_value} (YTD: {ytd_value})"
                    )
                elif len(matches) == 1:
                    # Only one value found: assume it's YTD only, skip extraction
                    ytd_value = matches[0]
                    self.logger.debug(
                        f"{field_name} YTD only found in line {line_num}: {ytd_value} - skipping extraction"
                    )

    def _extract_deductions(self, line: str, line_num: int, row: dict[str, Any]) -> None:
        """Extract deduction information from line."""
        deduction_patterns = {
            "hsa plan": "hsa_plan",
            "illness plan lo": "illness_plan",
            "illness plan": "illness_plan",
            "legal": "legal",
            "life ins": "life_insurance",
            "life insurance": "life_insurance",
            "pretax dental": "pretax_dental",
            "pretax medical": "pretax_medical",
            "pretax vision": "pretax_vision",
            "dep care": "dep_care",
            "vol acc 40/20": "vol_acc_40_20",
            "vol acc 20/10": "vol_acc_40_20",
            "vol child life": "vol_child_life",
            "vol spousl life": "vol_spousal_life",
            "401k pretax": "k401_pretax",
            "espp": "espp",
            "401k loan gp1": "k401_loan_gp1",
        }

        line_lower = line.lower()
        for pattern, field_name in deduction_patterns.items():
            if pattern in line_lower:
                self.logger.debug(f"Found deduction pattern '{pattern}' in line {line_num}: '{line}'")
                # Skip if we already extracted this field from this line
                if field_name in row:
                    self.logger.debug(f"Skipping {field_name} - already extracted")
                    continue

                if field_name == "hsa_plan":
                    # Special handling for HSA Plan format: "Hsa Plan -314 58* 1 887 48"
                    # Look for the pattern with asterisk (current period) and YTD
                    matches = re.findall(r"(-?\d+ \d+)\*", line)
                    self.logger.debug(f"HSA Plan deduction matches: {matches}")

                    if len(matches) >= 1:
                        # Extract current period value (with asterisk) - always store as positive
                        current_period_value = matches[0]
                        value = current_period_value.lstrip("-")  # Remove any negative sign
                        deduction_value = self._convert_pdf_number(value)
                        row[field_name] = deduction_value
                        self.logger.debug(
                            f"Extracted {field_name} (current period) from line {line_num}: {deduction_value}"
                        )
                        break
                elif field_name == "espp":
                    # Special handling for ESPP format: "Espp -467 80 1 403 40" or "Espp -55 42"
                    matches = re.findall(r"(-?\d+ \d+)", line)
                    self.logger.debug(f"ESPP deduction matches: {matches}")

                    if len(matches) >= 2:
                        # Two values found: first is current period, second is YTD
                        current_period_value = matches[0]
                        ytd_value = matches[1]
                        value = current_period_value.lstrip("-")  # Remove any negative sign
                        deduction_value = self._convert_pdf_number(value)
                        row[field_name] = deduction_value
                        self.logger.debug(
                            f"Extracted ESPP (current period) from line {line_num}: {deduction_value} (YTD: {ytd_value})"
                        )
                        break
                    elif len(matches) == 1:
                        # Only one value found: assume it's YTD only, skip extraction
                        ytd_value = matches[0]
                        self.logger.debug(f"ESPP YTD only found in line {line_num}: {ytd_value} - skipping extraction")
                        break
                elif field_name == "legal" or field_name == "k401_pretax" or field_name == "k401_loan_gp1":
                    # Special handling for larger numbers
                    matches = re.findall(r"(-?\d{1,3}(?: \d{3})* \d{2})", line)
                    self.logger.debug(f"Large number deduction matches for {field_name}: {matches}")

                    if len(matches) >= 2:
                        # Two values found: first is current period, second is YTD
                        current_period_value = matches[0]
                        ytd_value = matches[1]
                        value = current_period_value.lstrip("-")  # Remove any negative sign
                        deduction_value = self._convert_pdf_number(value)
                        row[field_name] = deduction_value
                        self.logger.debug(
                            f"Extracted {field_name} (current period) from line {line_num}: {deduction_value} (YTD: {ytd_value})"
                        )
                        break
                    elif len(matches) == 1:
                        # Only one value found: assume it's YTD only, skip extraction
                        ytd_value = matches[0]
                        self.logger.debug(
                            f"{field_name} YTD only found in line {line_num}: {ytd_value} - skipping extraction"
                        )
                        break
                else:
                    # Standard decimal pattern
                    matches = re.findall(r"(-?\d+[ .]\d{2})", line)
                    self.logger.debug(f"Standard deduction matches for {field_name}: {matches}")

                    if len(matches) >= 2:
                        # Two values found: first is current period, second is YTD
                        current_period_value = matches[0]
                        ytd_value = matches[1]
                        value = current_period_value.lstrip("-")  # Remove any negative sign
                        deduction_value = self._convert_pdf_number(value)
                        row[field_name] = deduction_value
                        self.logger.debug(
                            f"Extracted {field_name} (current period) from line {line_num}: {deduction_value} (YTD: {ytd_value})"
                        )
                        break
                    elif len(matches) == 1:
                        # Only one value found: assume it's YTD only, skip extraction
                        ytd_value = matches[0]
                        self.logger.debug(
                            f"{field_name} YTD only found in line {line_num}: {ytd_value} - skipping extraction"
                        )
                        break

    def _extract_bonus_deductions(self, line: str, line_num: int, row: dict[str, Any]) -> None:
        """Extract deductions for bonus paychecks (ESPP and 401K pretax)."""
        line_lower = line.lower()

        # Extract ESPP
        if "espp" in line_lower:
            self.logger.debug(f"Found ESPP pattern in line {line_num}: '{line}'")
            # Skip if we already extracted this field from this line
            if "espp" in row:
                self.logger.debug("Skipping ESPP - already extracted")
            else:
                # Special handling for ESPP format: "Espp -467 80 1 403 40" or "Espp -55 42"
                # Handle both 2-number and 3-number formats
                # First try to find the pattern with word boundaries to ensure proper separation
                matches = re.findall(r"(-?\d+ \d+)(?:\s+(\d+ \d+(?:\s+\d+)?))?", line)
                self.logger.debug(f"ESPP deduction matches: {matches}")

                if len(matches) >= 1 and len(matches[0]) >= 2 and matches[0][1]:
                    # Two values found: first is current period, second is YTD
                    current_period_value = matches[0][0]
                    ytd_value = matches[0][1]
                    value = current_period_value.lstrip("-")  # Remove any negative sign
                    deduction_value = self._convert_pdf_number(value)
                    row["espp"] = deduction_value
                    self.logger.debug(
                        f"Extracted ESPP (current period) from line {line_num}: {deduction_value} (YTD: {ytd_value})"
                    )
                elif len(matches) >= 1 and len(matches[0]) >= 1:
                    # Only one value found: assume it's YTD only, skip extraction
                    ytd_value = matches[0][0]
                    self.logger.debug(f"ESPP YTD only found in line {line_num}: {ytd_value} - skipping extraction")

        # Extract 401K pretax
        if "401k pretax" in line_lower:
            self.logger.debug(f"Found 401K pretax pattern in line {line_num}: '{line}'")
            # Skip if we already extracted this field from this line
            if "k401_pretax" in row:
                self.logger.debug("Skipping 401K pretax - already extracted")
            else:
                # Special handling for larger numbers (401K pretax can be large amounts)
                matches = re.findall(r"(-?\d{1,3}(?: \d{3})* \d{2})", line)
                self.logger.debug(f"401K pretax deduction matches: {matches}")

                if len(matches) >= 2:
                    # Two values found: first is current period, second is YTD
                    current_period_value = matches[0]
                    ytd_value = matches[1]
                    value = current_period_value.lstrip("-")  # Remove any negative sign
                    deduction_value = self._convert_pdf_number(value)
                    row["k401_pretax"] = deduction_value
                    self.logger.debug(
                        f"Extracted 401K pretax (current period) from line {line_num}: {deduction_value} (YTD: {ytd_value})"
                    )
                elif len(matches) == 1:
                    # Only one value found: assume it's YTD only, skip extraction
                    ytd_value = matches[0]
                    self.logger.debug(
                        f"401K pretax YTD only found in line {line_num}: {ytd_value} - skipping extraction"
                    )

    def _extract_vacation_deductions(self, line: str, line_num: int, row: dict[str, Any]) -> None:
        """Extract deductions for vacation paychecks (statutory deductions and 401K pretax only)."""
        line_lower = line.lower()

        # Define patterns for statutory deductions and 401K pretax
        deduction_patterns = {
            "federal income tax": "federal_income_tax",
            "social security tax": "social_security_tax",
            "medicare tax": "medicare_tax",
            "oh state income tax": "state_income_tax",
            "nc state income tax": "state_income_tax",
            "brooklyn income tax": "local_income_tax",
            "cleveland income tax": "local_income_tax",
            "401k pretax": "k401_pretax",
        }

        for pattern, field_name in deduction_patterns.items():
            if pattern in line_lower:
                self.logger.debug(f"Found vacation deduction pattern '{pattern}' in line {line_num}: '{line}'")
                # Skip if we already extracted this field from this line
                if field_name in row:
                    self.logger.debug(f"Skipping {field_name} - already extracted")
                    continue

                if field_name == "k401_pretax":
                    # Special handling for larger numbers (401K pretax can be large amounts)
                    matches = re.findall(r"(-?\d{1,3}(?: \d{3})* \d{2})", line)
                    self.logger.debug(f"401K pretax deduction matches: {matches}")

                    if len(matches) >= 2:
                        # Two values found: first is current period, second is YTD
                        current_period_value = matches[0]
                        ytd_value = matches[1]
                        value = current_period_value.lstrip("-")  # Remove any negative sign
                        deduction_value = self._convert_pdf_number(value)
                        row[field_name] = deduction_value
                        self.logger.debug(
                            f"Extracted 401K pretax (current period) from line {line_num}: {deduction_value} (YTD: {ytd_value})"
                        )
                        break
                    elif len(matches) == 1:
                        # Only one value found: assume it's YTD only, skip extraction
                        ytd_value = matches[0]
                        self.logger.debug(
                            f"401K pretax YTD only found in line {line_num}: {ytd_value} - skipping extraction"
                        )
                        break
                else:
                    # Standard tax deduction pattern
                    matches = re.findall(r"(-?\d{1,3}(?: \d{3})* \d{2})", line)
                    self.logger.debug(f"Tax deduction matches for {field_name}: {matches}")

                    if len(matches) >= 2:
                        # Two values found: first is current period, second is YTD
                        current_period_value = matches[0]
                        ytd_value = matches[1]
                        value = current_period_value.lstrip("-")  # Remove any negative sign
                        deduction_value = self._convert_pdf_number(value)
                        row[field_name] = deduction_value
                        self.logger.debug(
                            f"Extracted {field_name} (current period) from line {line_num}: {deduction_value} (YTD: {ytd_value})"
                        )
                        break
                    elif len(matches) == 1:
                        # Only one value found: assume it's YTD only, skip extraction
                        ytd_value = matches[0]
                        self.logger.debug(
                            f"{field_name} YTD only found in line {line_num}: {ytd_value} - skipping extraction"
                        )
                        break

    def _extract_net_pay(self, line: str, line_num: int, row: dict[str, Any]) -> None:
        """Extract net pay from line."""
        if "net pay" in line.lower():
            self.logger.debug(f"Found 'net pay' in line {line_num}: '{line}'")
            matches = re.findall(r"(\d+ \d+(?: \d+)?)", line)
            self.logger.debug(f"Net pay matches: {matches}")

            if len(matches) >= 2:
                # Two values found: first is current period, second is YTD
                current_period_value = self._convert_pdf_number(matches[0])
                ytd_value = self._convert_pdf_number(matches[1])
                row["net_pay"] = current_period_value
                self.logger.debug(
                    f"Extracted Net Pay (current period) from line {line_num}: {current_period_value} (YTD: {ytd_value})"
                )
            elif len(matches) == 1:
                # Only one value found: this is the current period net pay (Net Pay is always current period)
                current_period_value = self._convert_pdf_number(matches[0])
                row["net_pay"] = current_period_value
                self.logger.debug(f"Extracted Net Pay (current period) from line {line_num}: {current_period_value}")
            else:
                self.logger.debug(f"No net pay pattern match found in line {line_num}")

    def _validate_paycheck_calculations(
        self, transaction_data: dict[str, Any], is_bonus_paycheck: bool, is_vacation_paycheck: bool = False
    ) -> None:
        """
        Validate paycheck calculations and throw exception if mismatch.

        For regular paychecks: Net pay = Gross pay - statutory deductions - other deductions
        For bonus paychecks: Net pay = Bonus - statutory deductions - ESPP (if present) - 401K pretax (if present)
        For vacation paychecks: Net pay = Vacation (other_income) - statutory deductions - 401K pretax (if present)

        Args:
            transaction_data: The extracted transaction data
            is_bonus_paycheck: Whether this is a bonus paycheck
            is_vacation_paycheck: Whether this is a vacation paycheck

        Raises:
            ValueError: If calculations don't match within $0.01 tolerance
        """
        try:
            if is_bonus_paycheck:
                # Bonus paycheck validation
                bonus_amount = float(transaction_data.get("bonus", 0) or 0)
                if bonus_amount == 0:
                    self.logger.warning("Bonus paycheck has no bonus amount - skipping validation")
                    return

                # Calculate expected net pay: Bonus - statutory deductions - ESPP (if present) - 401K pretax (if present)
                statutory_deductions = self._sum_statutory_deductions(transaction_data)
                espp_deduction = float(transaction_data.get("espp", 0) or 0)
                k401_pretax_deduction = float(transaction_data.get("k401_pretax", 0) or 0)
                expected_net_pay = bonus_amount - statutory_deductions - espp_deduction - k401_pretax_deduction
                actual_net_pay = float(transaction_data.get("net_pay", 0) or 0)

                self.logger.debug(
                    f"Bonus paycheck validation: Bonus ${bonus_amount:.2f} - Statutory ${statutory_deductions:.2f} - ESPP ${espp_deduction:.2f} - 401K Pretax ${k401_pretax_deduction:.2f} = Expected Net ${expected_net_pay:.2f}, Actual Net ${actual_net_pay:.2f}"
                )

                if abs(expected_net_pay - actual_net_pay) > 0.01:
                    error_msg = (
                        f"Bonus paycheck validation FAILED for {transaction_data.get('source_file', 'unknown')}: "
                        f"Expected net pay ${expected_net_pay:.2f} (Bonus ${bonus_amount:.2f} - Statutory ${statutory_deductions:.2f} - ESPP ${espp_deduction:.2f} - 401K Pretax ${k401_pretax_deduction:.2f}), "
                        f"but got ${actual_net_pay:.2f}. Difference: ${abs(expected_net_pay - actual_net_pay):.2f}"
                    )
                    self.logger.error(error_msg)
                    raise ValueError(error_msg)
                else:
                    self.logger.info(
                        f"Bonus paycheck validation PASSED: Net pay ${actual_net_pay:.2f} matches expected ${expected_net_pay:.2f}"
                    )
            elif is_vacation_paycheck:
                # Vacation paycheck validation
                vacation_amount = float(transaction_data.get("other_income", 0) or 0)
                if vacation_amount == 0:
                    self.logger.warning("Vacation paycheck has no vacation amount - skipping validation")
                    return

                # Calculate expected net pay: Vacation - statutory deductions - 401K pretax (if present)
                statutory_deductions = self._sum_statutory_deductions(transaction_data)
                k401_pretax_deduction = float(transaction_data.get("k401_pretax", 0) or 0)
                expected_net_pay = vacation_amount - statutory_deductions - k401_pretax_deduction
                actual_net_pay = float(transaction_data.get("net_pay", 0) or 0)

                self.logger.debug(
                    f"Vacation paycheck validation: Vacation ${vacation_amount:.2f} - Statutory ${statutory_deductions:.2f} - 401K Pretax ${k401_pretax_deduction:.2f} = Expected Net ${expected_net_pay:.2f}, Actual Net ${actual_net_pay:.2f}"
                )

                if abs(expected_net_pay - actual_net_pay) > 0.01:
                    error_msg = (
                        f"Vacation paycheck validation FAILED for {transaction_data.get('source_file', 'unknown')}: "
                        f"Expected net pay ${expected_net_pay:.2f} (Vacation ${vacation_amount:.2f} - Statutory ${statutory_deductions:.2f} - 401K Pretax ${k401_pretax_deduction:.2f}), "
                        f"but got ${actual_net_pay:.2f}. Difference: ${abs(expected_net_pay - actual_net_pay):.2f}"
                    )
                    self.logger.error(error_msg)
                    raise ValueError(error_msg)
                else:
                    self.logger.info(
                        f"Vacation paycheck validation PASSED: Net pay ${actual_net_pay:.2f} matches expected ${expected_net_pay:.2f}"
                    )
            else:
                # Regular paycheck validation
                regular_pay = float(transaction_data.get("regular_pay", 0) or 0)
                other_income = float(transaction_data.get("other_income", 0) or 0)
                gross_pay = regular_pay + other_income

                if gross_pay == 0:
                    self.logger.warning("Regular paycheck has no gross pay - skipping validation")
                    return

                # Calculate expected net pay: Gross pay - statutory deductions - other deductions
                statutory_deductions = self._sum_statutory_deductions(transaction_data)
                other_deductions = self._sum_other_deductions(transaction_data)
                expected_net_pay = gross_pay - statutory_deductions - other_deductions
                actual_net_pay = float(transaction_data.get("net_pay", 0) or 0)

                self.logger.debug(
                    f"Regular paycheck validation: Gross ${gross_pay:.2f} (Regular ${regular_pay:.2f} + Other ${other_income:.2f}) - Statutory ${statutory_deductions:.2f} - Other ${other_deductions:.2f} = Expected Net ${expected_net_pay:.2f}, Actual Net ${actual_net_pay:.2f}"
                )

                if abs(expected_net_pay - actual_net_pay) > 0.01:
                    error_msg = (
                        f"Regular paycheck validation FAILED for {transaction_data.get('source_file', 'unknown')}: "
                        f"Expected net pay ${expected_net_pay:.2f} (Gross ${gross_pay:.2f} - Statutory ${statutory_deductions:.2f} - Other ${other_deductions:.2f}), "
                        f"but got ${actual_net_pay:.2f}. Difference: ${abs(expected_net_pay - actual_net_pay):.2f}"
                    )
                    self.logger.error(error_msg)
                    raise ValueError(error_msg)
                else:
                    self.logger.info(
                        f"Regular paycheck validation PASSED: Net pay ${actual_net_pay:.2f} matches expected ${expected_net_pay:.2f}"
                    )

        except Exception as e:
            if isinstance(e, ValueError):
                raise  # Re-raise validation errors
            else:
                # Log unexpected errors but don't fail validation
                self.logger.error(f"Error during paycheck validation: {str(e)}")
                raise ValueError(f"Paycheck validation error: {str(e)}") from e

    def _sum_statutory_deductions(self, transaction_data: dict[str, Any]) -> float:
        """Sum all statutory deductions (taxes)."""
        statutory_fields = [
            "federal_income_tax",
            "social_security_tax",
            "medicare_tax",
            "state_income_tax",
            "local_income_tax",
        ]

        total = 0.0
        for field in statutory_fields:
            value = transaction_data.get(field, 0)
            if value:
                # Convert to float and handle negative values (deductions are stored as negative)
                try:
                    amount = float(value)
                    # Add absolute value since deductions are negative
                    total += abs(amount)
                except (ValueError, TypeError):
                    self.logger.warning(f"Could not parse statutory deduction {field}: {value}")

        return total

    def _sum_other_deductions(self, transaction_data: dict[str, Any]) -> float:
        """Sum all other deductions (benefits, 401K, etc.)."""
        other_deduction_fields = [
            "hsa_plan",
            "illness_plan",
            "legal",
            "life_insurance",
            "pretax_dental",
            "pretax_medical",
            "pretax_vision",
            "dep_care",
            "vol_acc_40_20",
            "vol_child_life",
            "vol_spousal_life",
            "k401_pretax",
            "espp",
            "k401_loan_gp1",
        ]

        total = 0.0
        for field in other_deduction_fields:
            value = transaction_data.get(field, 0)
            if value:
                # Convert to float and handle negative values (deductions are stored as negative)
                try:
                    amount = float(value)
                    # Add absolute value since deductions are negative
                    total += abs(amount)
                except (ValueError, TypeError):
                    self.logger.warning(f"Could not parse other deduction {field}: {value}")

        return total

    def _parse_amount(self, amount_str: str) -> float | None:
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
