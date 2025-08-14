"""Main processor for handling statement operations."""

from pathlib import Path

from loguru import logger

from .config import Config
from .database import DatabaseManager
from .institutions.base import BaseInstitution
from .institutions.cash_app import CashAppInstitution
from .institutions.first_energy import FirstEnergyInstitution
from .institutions.icici import ICICIInstitution
from .institutions.ipay import IPayInstitution
from .institutions.robinhood import RobinhoodInstitution


class StatementProcessor:
    """Main processor for handling statement operations."""

    def __init__(self, financial_institution: str, config: Config):
        """Initialize the processor with institution and configuration."""
        self.financial_institution = financial_institution
        self.config = config
        self.logger = logger.bind(name=f"Processor.{financial_institution}")

        # Initialize database manager
        self.db_manager = DatabaseManager(config.database)

        # Get institution handler
        self.institution = self._get_institution_handler()

        self.logger.info(f"Initialized processor for {financial_institution}")

    def _get_institution_handler(self) -> BaseInstitution:
        """Get the appropriate institution handler."""
        institution_map = {
            "ipay": IPayInstitution,
            "icici": ICICIInstitution,
            "robinhood": RobinhoodInstitution,
            "first-energy": FirstEnergyInstitution,
            "cash-app": CashAppInstitution,
        }

        handler_class = institution_map.get(self.financial_institution)
        if not handler_class:
            raise ValueError(f"Unsupported financial institution: {self.financial_institution}")

        institution_config = self.config.get_institution_config(self.financial_institution)
        return handler_class(institution_config, self.db_manager)

    def rename_files(self, input_folder: Path) -> None:
        """Rename and organize statement files by year based on their date."""
        self.logger.info("Starting file rename and organize process")
        self.logger.info(f"Input folder: {input_folder}")
        self.logger.info(f"Target folder: {self.config.target_statements_folder}")

        if not input_folder.exists():
            raise FileNotFoundError(f"Input folder not found: {input_folder}")

        # Get all PDF files in the folder
        pdf_files = list(input_folder.glob("*.pdf"))
        if not pdf_files:
            self.logger.warning(f"No PDF files found in {input_folder}")
            return

        self.logger.info(f"Found {len(pdf_files)} PDF files to process")

        for pdf_file in pdf_files:
            try:
                self.logger.debug(f"Processing file: {pdf_file.name}")

                # Skip files with "manual_entry" in the filename
                if "manual_entry" in pdf_file.name.lower():
                    self.logger.info(f"Skipping manual entry file: {pdf_file.name}")
                    continue

                # Extract date from statement
                statement_date = self.institution.extract_statement_date(pdf_file)

                if statement_date:
                    # Determine payment type based on input filename conventions
                    payment_type = self._determine_payment_type_from_filename(pdf_file.name)

                    # Create new filename with payment type: YYYY-MM-DD-{type}.pdf
                    base_filename = f"{statement_date.strftime('%Y-%m-%d')}"
                    if payment_type:
                        new_filename = f"{base_filename}-{payment_type}.pdf"
                    else:
                        new_filename = f"{base_filename}.pdf"

                    year = statement_date.year

                    # Get target folder for this institution and year
                    target_folder = self.config.get_target_folder(self.financial_institution, year)
                    new_filepath = target_folder / new_filename

                    # Check if file already exists in target location
                    if new_filepath.exists():
                        self.logger.warning(
                            f"File {new_filename} already exists in {target_folder}, skipping {pdf_file.name}"
                        )
                        continue

                    # Move the file to the target location
                    pdf_file.rename(new_filepath)
                    self.logger.info(f"Moved {pdf_file.name} to {new_filepath} (type: {payment_type})")
                else:
                    self.logger.warning(f"Could not extract date from {pdf_file.name}")

            except Exception as e:
                self.logger.error(f"Error processing {pdf_file.name}: {str(e)}")

        self.logger.info("File rename and organize process completed")

    def _determine_payment_type(self, pdf_file: Path) -> str | None:
        """Determine the type of payment from the PDF content."""
        try:
            # Extract text from PDF to analyze the bonus pattern
            import pdfplumber

            with pdfplumber.open(pdf_file) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)

            # Debug: Show the full text to see what we're working with
            self.logger.debug(f"Full text from {pdf_file.name}:")
            self.logger.debug("=" * 80)
            self.logger.debug(text)
            self.logger.debug("=" * 80)

            lines = text.splitlines()

            for i, line in enumerate(lines):
                if "bonus" in line.lower():
                    self.logger.debug(f"Found bonus line {i}: '{line}'")
                    # Check for the specific pattern that indicates actual bonus paycheck
                    # "Bonus 1 477 00 1 477 00 Your federal taxable wages this period are"
                    import re

                    bonus_matches = re.findall(r"(\d+ \d+ \d+)", line)
                    self.logger.debug(f"Bonus matches in line {i}: {bonus_matches}")

                    if len(bonus_matches) >= 2 and bonus_matches[0] == bonus_matches[1]:
                        # This is an actual bonus paycheck
                        self.logger.debug(f"Detected bonus paycheck pattern in {pdf_file.name}: {line}")
                        return "bonus"
                    elif len(bonus_matches) == 1:
                        # This is a regular paycheck with YTD bonus reporting
                        self.logger.debug(
                            f"Detected regular paycheck with YTD bonus reporting in {pdf_file.name}: {line}"
                        )
                        return "regular"
                elif "vacation" in line.lower():
                    self.logger.debug(f"Found vacation line {i}: '{line}'")
                    # Check for the specific pattern that indicates actual vacation paycheck
                    import re

                    vacation_matches = re.findall(r"(\d+ \d+ \d+)", line)
                    self.logger.debug(f"Vacation matches in line {i}: {vacation_matches}")

                    if len(vacation_matches) >= 2 and vacation_matches[0] == vacation_matches[1]:
                        # This is an actual vacation paycheck
                        self.logger.debug(f"Detected vacation paycheck pattern in {pdf_file.name}: {line}")
                        return "vacation"
                    elif len(vacation_matches) == 1:
                        # This is a regular paycheck with YTD vacation reporting
                        self.logger.debug(
                            f"Detected regular paycheck with YTD vacation reporting in {pdf_file.name}: {line}"
                        )
                        return "regular"
                else:
                    # Debug: Show lines that might contain bonus or vacation but don't match our pattern
                    if any(word in line.lower() for word in ["bonus", "vacation", "pay", "wage", "taxable"]):
                        self.logger.debug(f"Relevant line {i}: '{line}'")

            # If no bonus or vacation line found, it's a regular paycheck
            self.logger.debug(f"No bonus or vacation line found in {pdf_file.name}, treating as regular paycheck")
            return "regular"

        except Exception as e:
            self.logger.debug(f"Error determining payment type for {pdf_file.name}: {str(e)}")
            return "regular"  # Default to regular if analysis fails

    def _determine_payment_type_from_filename(self, filename: str) -> str:
        """Determine payment type based on input filename conventions."""
        filename_lower = filename.lower()

        # Debug logging
        self.logger.debug(f"Checking filename: '{filename}' -> lowercase: '{filename_lower}'")
        self.logger.debug(f"Contains 'ytd': {'ytd' in filename_lower}")
        self.logger.debug(f"Contains 'bonus': {'bonus' in filename_lower}")
        self.logger.debug(f"Contains 'vacation': {'vacation' in filename_lower}")

        # Check for bonus files (anywhere in filename)
        if "bonus" in filename_lower:
            self.logger.info(f"Detected bonus file from filename: {filename}")
            return "bonus"

        # Check for vacation files (anywhere in filename)
        if "vacation" in filename_lower:
            self.logger.info(f"Detected vacation file from filename: {filename}")
            return "vacation"

        # Check for YTD files (anywhere in filename)
        if "ytd" in filename_lower:
            self.logger.info(f"Detected YTD file from filename: {filename}")
            return "ye-summary"

        # Default to regular for all other files
        self.logger.info(f"Detected regular file from filename: {filename}")
        return "regular"

    def extract_transactions_from_organized(self) -> None:
        """Extract transactions from already organized statements (without renaming first)."""
        self.logger.info("Starting transaction extraction from organized files")

        # Find all PDF files in the target folder for this institution
        target_base = Path(self.config.target_statements_folder).expanduser()
        institution_folder = target_base / self.financial_institution

        if not institution_folder.exists():
            self.logger.warning(f"No organized files found for {self.financial_institution}")
            return

        # Get all PDF files from all year folders for this institution
        pdf_files = []
        for year_folder in institution_folder.iterdir():
            if year_folder.is_dir():
                year_pdfs = list(year_folder.glob("*.pdf"))
                pdf_files.extend(year_pdfs)

        if not pdf_files:
            self.logger.warning(f"No PDF files found in organized folders for {self.financial_institution}")
            return

        # Sort PDF files chronologically by their names (yyyy-mm-dd format)
        def extract_date_from_filename(filename: str) -> tuple:
            """Extract date components from filename for sorting."""
            try:
                # Extract date part from filename (e.g., "2025-01-15-regular.pdf" -> "2025-01-15")
                date_part = filename.split("-")[:3]  # Take first 3 parts: year, month, day
                if len(date_part) == 3 and all(part.isdigit() for part in date_part):
                    year, month, day = map(int, date_part)
                    return (year, month, day)
                else:
                    # If filename doesn't match expected format, put it at the end
                    return (9999, 12, 31)
            except (ValueError, IndexError):
                # If parsing fails, put it at the end
                return (9999, 12, 31)

        # Sort files chronologically by date in filename
        pdf_files.sort(key=lambda x: extract_date_from_filename(x.name))

        # Log the processing order
        self.logger.info(f"Found {len(pdf_files)} PDF files to extract transactions from")
        self.logger.info("Files will be processed in chronological order:")
        for i, pdf_file in enumerate(pdf_files, 1):
            if not pdf_file.name.endswith("-ye-summary.pdf"):
                self.logger.info(f"  {i}. {pdf_file.name}")

        for pdf_file in pdf_files:
            try:
                # Skip YTD files (they don't need transaction extraction)
                if pdf_file.name.endswith("-ye-summary.pdf"):
                    self.logger.info(f"Skipping YTD file (no transaction extraction needed): {pdf_file.name}")
                    continue

                # Skip files with "manual_entry" in the filename
                if "manual_entry" in pdf_file.name.lower():
                    self.logger.info(f"Skipping manual entry file: {pdf_file.name}")
                    continue

                self.logger.debug(f"Extracting transactions from: {pdf_file.name}")

                # Extract transactions from statement
                transactions = self.institution.extract_transactions(pdf_file)

                if transactions:
                    # Store transactions in database
                    self.db_manager.store_transactions(transactions)
                    self.logger.info(f"Stored {len(transactions)} transactions from {pdf_file.name}")
                else:
                    self.logger.warning(f"No transactions found in {pdf_file.name}")

            except Exception as e:
                self.logger.error(f"Error extracting transactions from {pdf_file.name}: {str(e)}")

        self.logger.info("Transaction extraction from organized files completed")

    def extract_transactions(self, input_folder: Path) -> None:
        """Extract transactions from statements and store in database."""
        self.logger.info(f"Starting transaction extraction for {input_folder}")

        # First rename files to ensure proper naming
        self.rename_files(input_folder)

        # After renaming, files are now in the target folder organized by year
        # We need to find all PDF files in the target folder for this institution
        target_base = Path(self.config.target_statements_folder).expanduser()
        institution_folder = target_base / self.financial_institution

        if not institution_folder.exists():
            self.logger.warning(f"No organized files found for {self.financial_institution}")
            return

        # Get all PDF files from all year folders for this institution
        pdf_files = []
        for year_folder in institution_folder.iterdir():
            if year_folder.is_dir():
                year_pdfs = list(year_folder.glob("*.pdf"))
                pdf_files.extend(year_pdfs)

        if not pdf_files:
            self.logger.warning(f"No PDF files found in organized folders for {self.financial_institution}")
            return

        # Sort PDF files chronologically by their names (yyyy-mm-dd format)
        def extract_date_from_filename(filename: str) -> tuple:
            """Extract date components from filename for sorting."""
            try:
                # Extract date part from filename (e.g., "2025-01-15-regular.pdf" -> "2025-01-15")
                date_part = filename.split("-")[:3]  # Take first 3 parts: year, month, day
                if len(date_part) == 3 and all(part.isdigit() for part in date_part):
                    year, month, day = map(int, date_part)
                    return (year, month, day)
                else:
                    # If filename doesn't match expected format, put it at the end
                    return (9999, 12, 31)
            except (ValueError, IndexError):
                # If parsing fails, put it at the end
                return (9999, 12, 31)

        # Sort files chronologically by date in filename
        pdf_files.sort(key=lambda x: extract_date_from_filename(x.name))

        # Log the processing order
        self.logger.info(f"Found {len(pdf_files)} PDF files to extract transactions from")
        self.logger.info("Files will be processed in chronological order:")
        for i, pdf_file in enumerate(pdf_files, 1):
            if not pdf_file.name.endswith("-ye-summary.pdf"):
                self.logger.info(f"  {i}. {pdf_file.name}")

        for pdf_file in pdf_files:
            try:
                # Skip YTD files (they don't need transaction extraction)
                if pdf_file.name.endswith("-ye-summary.pdf"):
                    self.logger.info(f"Skipping YTD file (no transaction extraction needed): {pdf_file.name}")
                    continue

                # Skip files with "manual_entry" in the filename
                if "manual_entry" in pdf_file.name.lower():
                    self.logger.info(f"Skipping manual entry file: {pdf_file.name}")
                    continue

                self.logger.debug(f"Extracting transactions from: {pdf_file.name}")

                # Extract transactions from statement
                transactions = self.institution.extract_transactions(pdf_file)

                if transactions:
                    # Store transactions in database
                    self.db_manager.store_transactions(transactions)
                    self.logger.info(f"Stored {len(transactions)} transactions from {pdf_file.name}")
                else:
                    self.logger.warning(f"No transactions found in {pdf_file.name}")

            except Exception as e:
                self.logger.error(f"Error extracting transactions from {pdf_file.name}: {str(e)}")
                # If this is a validation error, stop processing all files as required by README
                if "validation" in str(e).lower() or "mismatch" in str(e).lower():
                    self.logger.error(
                        "CRITICAL: Paycheck validation failed. Stopping processing as required by README."
                    )
                    raise

        self.logger.info("Transaction extraction completed")

    def generate_excel(self, input_folder: Path) -> None:
        """Generate Excel file with extracted transactions."""
        self.logger.info("Starting Excel generation")

        try:
            # Get all transactions from database
            transactions = self.db_manager.get_all_transactions(self.financial_institution)

            if not transactions:
                self.logger.warning("No transactions found in database")
                return

            # Generate Excel file in the target folder for this institution
            target_base = Path(self.config.target_statements_folder).expanduser()
            institution_folder = target_base / self.financial_institution
            institution_folder.mkdir(parents=True, exist_ok=True)

            output_file = institution_folder / f"{self.financial_institution}_transactions.xlsx"
            self.institution.generate_excel(transactions, output_file)

            self.logger.info(f"Generated Excel file: {output_file}")

        except Exception as e:
            self.logger.error(f"Error generating Excel file: {str(e)}")
            raise

    def export_to_excel(self) -> None:
        """Export transactions from database to Excel file."""
        self.logger.info("Starting database export to Excel")

        try:
            # Get all transactions from database
            transactions = self.db_manager.get_all_transactions(self.financial_institution)

            if not transactions:
                self.logger.warning("No transactions found in database")
                return

            # Create output directory if target folder is configured
            if self.config.target_statements_folder:
                target_base = Path(self.config.target_statements_folder).expanduser()
                institution_folder = target_base / self.financial_institution
                institution_folder.mkdir(parents=True, exist_ok=True)
                output_file = institution_folder / f"{self.financial_institution}_export.xlsx"
            else:
                # Default to current directory if no target folder configured
                output_file = Path(f"{self.financial_institution}_export.xlsx")

            self.institution.generate_excel(transactions, output_file)

            self.logger.info(f"Exported Excel file: {output_file}")

        except Exception as e:
            self.logger.error(f"Error exporting to Excel: {str(e)}")
            raise

    def enter_to_quicken(self) -> None:
        """Enter transactions into Quicken application."""
        self.logger.info("Starting Quicken integration")

        if not self.config.quicken.enabled:
            self.logger.warning("Quicken integration is not enabled in configuration")
            return

        try:
            # Get transactions from database
            transactions = self.db_manager.get_all_transactions(self.financial_institution)

            if not transactions:
                self.logger.warning("No transactions found in database")
                return

            # Enter transactions into Quicken
            self.institution.enter_to_quicken(transactions, self.config.quicken)

            self.logger.info("Successfully entered transactions into Quicken")

        except Exception as e:
            self.logger.error(f"Error entering transactions into Quicken: {str(e)}")
            raise

    def reconcile_ytd_transactions(self, year_param: str) -> None:
        """Reconcile YTD transactions for a specific year or month-year."""
        self.logger.info(f"Starting YTD reconciliation for {year_param}")

        try:
            # Parse the year parameter to determine if it's YYYY or MM-YYYY
            if "-" in year_param:
                # Format: MM-YYYY
                try:
                    month_str, year_str = year_param.split("-")
                    month = int(month_str)
                    year = int(year_str)

                    if month < 1 or month > 12:
                        raise ValueError(f"Invalid month: {month}")

                    self.logger.info(f"Reconciling transactions up to {month:02d}-{year}")
                    transactions = self.db_manager.get_transactions_by_month_year(
                        self.financial_institution, month, year
                    )
                    reconciliation_period = f"{month:02d}-{year}"
                except ValueError as e:
                    raise ValueError(
                        f"Invalid month-year format '{year_param}'. Expected MM-YYYY (e.g., 06-2024): {e}"
                    ) from e
            else:
                # Format: YYYY
                try:
                    year = int(year_param)
                    self.logger.info(f"Reconciling transactions for entire year {year}")
                    transactions = self.db_manager.get_transactions_by_year(self.financial_institution, year)
                    reconciliation_period = str(year)
                except ValueError as e:
                    raise ValueError(f"Invalid year format '{year_param}'. Expected YYYY (e.g., 2024): {e}") from e

            if not transactions:
                self.logger.warning(f"No transactions found for year {year}")
                return

            # Calculate earnings
            total_regular_pay = sum(float(t.get("regular_pay", 0) or 0) for t in transactions)
            total_bonus = sum(float(t.get("bonus", 0) or 0) for t in transactions)
            total_other_income = sum(float(t.get("other_income", 0) or 0) for t in transactions)
            total_gross_pay_from_table = sum(float(t.get("gross_pay", 0) or 0) for t in transactions)
            total_net_pay_from_table = sum(float(t.get("net_pay", 0) or 0) for t in transactions)

            # Note: Gross pay is now extracted directly from PDF, not calculated
            # This calculation is kept for validation purposes only
            calculated_gross_pay = total_regular_pay + total_bonus + total_other_income

            # Calculate statutory deductions
            total_federal_tax = sum(float(t.get("federal_income_tax", 0) or 0) for t in transactions)
            total_social_security = sum(float(t.get("social_security_tax", 0) or 0) for t in transactions)
            total_medicare = sum(float(t.get("medicare_tax", 0) or 0) for t in transactions)
            total_state_tax = sum(float(t.get("state_income_tax", 0) or 0) for t in transactions)
            total_local_tax = sum(float(t.get("local_income_tax", 0) or 0) for t in transactions)

            total_statutory_deductions = (
                total_federal_tax + total_social_security + total_medicare + total_state_tax + total_local_tax
            )

            # Calculate other deductions
            total_hsa = sum(float(t.get("hsa_plan", 0) or 0) for t in transactions)
            total_illness_plan = sum(float(t.get("illness_plan", 0) or 0) for t in transactions)
            total_legal = sum(float(t.get("legal", 0) or 0) for t in transactions)
            total_life_insurance = sum(float(t.get("life_insurance", 0) or 0) for t in transactions)
            total_pretax_dental = sum(float(t.get("pretax_dental", 0) or 0) for t in transactions)
            total_pretax_medical = sum(float(t.get("pretax_medical", 0) or 0) for t in transactions)
            total_pretax_vision = sum(float(t.get("pretax_vision", 0) or 0) for t in transactions)
            total_dep_care = sum(float(t.get("dep_care", 0) or 0) for t in transactions)
            total_vol_acc_40_20 = sum(float(t.get("vol_acc_40_20", 0) or 0) for t in transactions)
            total_vol_child_life = sum(float(t.get("vol_child_life", 0) or 0) for t in transactions)
            total_vol_spousal_life = sum(float(t.get("vol_spousal_life", 0) or 0) for t in transactions)
            total_401k_pretax = sum(float(t.get("k401_pretax", 0) or 0) for t in transactions)
            total_espp = sum(float(t.get("espp", 0) or 0) for t in transactions)
            total_401k_loan_gp1 = sum(float(t.get("k401_loan_gp1", 0) or 0) for t in transactions)
            total_taxable_off = sum(float(t.get("taxable_off", 0) or 0) for t in transactions)

            total_other_deductions = (
                total_hsa
                + total_illness_plan
                + total_legal
                + total_life_insurance
                + total_pretax_dental
                + total_pretax_medical
                + total_pretax_vision
                + total_dep_care
                + total_vol_acc_40_20
                + total_vol_child_life
                + total_vol_spousal_life
                + total_401k_pretax
                + total_espp
                + total_401k_loan_gp1
                + total_taxable_off
            )

            # Calculate net pay (deductions are stored as positive values, so we subtract them)
            calculated_net_pay = calculated_gross_pay - total_statutory_deductions - total_other_deductions

            # Check if calculations match
            gross_pay_difference = calculated_gross_pay - total_gross_pay_from_table
            net_pay_difference = calculated_net_pay - total_net_pay_from_table
            gross_pay_matched = abs(gross_pay_difference) < 0.01
            net_pay_matched = abs(net_pay_difference) < 0.01

            # Print the reconciliation report
            self._print_ytd_reconciliation_report(
                year=reconciliation_period,
                transaction_count=len(transactions),
                total_regular_pay=total_regular_pay,
                total_bonus=total_bonus,
                total_other_income=total_other_income,
                calculated_gross_pay=calculated_gross_pay,
                total_gross_pay_from_table=total_gross_pay_from_table,
                gross_pay_matched=gross_pay_matched,
                total_federal_tax=total_federal_tax,
                total_social_security=total_social_security,
                total_medicare=total_medicare,
                total_state_tax=total_state_tax,
                total_local_tax=total_local_tax,
                total_statutory_deductions=total_statutory_deductions,
                total_hsa=total_hsa,
                total_illness_plan=total_illness_plan,
                total_legal=total_legal,
                total_life_insurance=total_life_insurance,
                total_pretax_dental=total_pretax_dental,
                total_pretax_medical=total_pretax_medical,
                total_pretax_vision=total_pretax_vision,
                total_dep_care=total_dep_care,
                total_vol_acc_40_20=total_vol_acc_40_20,
                total_vol_child_life=total_vol_child_life,
                total_vol_spousal_life=total_vol_spousal_life,
                total_401k_pretax=total_401k_pretax,
                total_espp=total_espp,
                total_401k_loan_gp1=total_401k_loan_gp1,
                total_taxable_off=total_taxable_off,
                total_other_deductions=total_other_deductions,
                calculated_net_pay=calculated_net_pay,
                total_net_pay_from_table=total_net_pay_from_table,
                net_pay_matched=net_pay_matched,
                gross_pay_difference=gross_pay_difference,
                net_pay_difference=net_pay_difference,
            )

            self.logger.info(f"YTD reconciliation completed for {reconciliation_period}")

        except Exception as e:
            self.logger.error(f"Error during YTD reconciliation: {str(e)}")
            raise

    def _print_ytd_reconciliation_report(self, **kwargs) -> None:
        """Print the YTD reconciliation report."""
        year = kwargs["year"]

        print(f"\nSum of Earnings YTD for {year} are:")
        print("=" * 50)
        print(f"{'Regular Pay':<30} ${kwargs['total_regular_pay']:>15,.2f}")
        print(f"{'Bonus':<30} ${kwargs['total_bonus']:>15,.2f}")
        print(f"{'Other Income':<30} ${kwargs['total_other_income']:>15,.2f}")
        print(f"{'Gross Pay (extracted from PDF)':<30} ${kwargs['total_gross_pay_from_table']:>15,.2f}")
        print(f"{'Gross Pay (calculated sum)':<30} ${kwargs['calculated_gross_pay']:>15,.2f}")
        if kwargs["gross_pay_matched"]:
            print(f"{'Matched?':<30} {'Yes':>15}")
        else:
            print(f"{'Matched?':<30} {'No':>15}")
            print(f"{'Difference':<30} ${kwargs['gross_pay_difference']:>15,.2f}")

        print("\nDeductions:")
        print("=" * 50)
        print("Deductions Statutory")
        print("-" * 50)
        print(f"{'Federal Income Tax':<30} -${abs(kwargs['total_federal_tax']):>14,.2f}")
        print(f"{'Social Security Tax':<30} -${abs(kwargs['total_social_security']):>14,.2f}")
        print(f"{'Medicare Tax':<30} -${abs(kwargs['total_medicare']):>14,.2f}")
        print(f"{'State Income Tax':<30} -${abs(kwargs['total_state_tax']):>14,.2f}")
        print(f"{'Local Income Tax':<30} -${abs(kwargs['total_local_tax']):>14,.2f}")
        print()
        print(f"{'Total Statutory Deductions':<30} -${abs(kwargs['total_statutory_deductions']):>14,.2f}")
        print("-" * 50)
        print()
        print("Other Deductions")
        print("-" * 50)
        print(f"{'HSA Plan':<30} -${abs(kwargs['total_hsa']):>14,.2f}")
        print(f"{'Illness Plan':<30} -${abs(kwargs['total_illness_plan']):>14,.2f}")
        print(f"{'Legal':<30} -${abs(kwargs['total_legal']):>14,.2f}")
        print(f"{'Life Insurance':<30} -${abs(kwargs['total_life_insurance']):>14,.2f}")
        print(f"{'Pretax Dental':<30} -${abs(kwargs['total_pretax_dental']):>14,.2f}")
        print(f"{'Pretax Medical':<30} -${abs(kwargs['total_pretax_medical']):>14,.2f}")
        print(f"{'Pretax Vision':<30} -${abs(kwargs['total_pretax_vision']):>14,.2f}")
        print(f"{'Dep Care':<30} -${abs(kwargs['total_dep_care']):>14,.2f}")
        print(f"{'Vol Acc 40/20/20/10':<30} -${abs(kwargs['total_vol_acc_40_20']):>14,.2f}")
        print(f"{'Vol Child Life':<30} -${abs(kwargs['total_vol_child_life']):>14,.2f}")
        print(f"{'Vol Spousal Life':<30} -${abs(kwargs['total_vol_spousal_life']):>14,.2f}")
        print(f"{'401K Pretax':<30} -${abs(kwargs['total_401k_pretax']):>14,.2f}")
        print(f"{'ESPP':<30} -${abs(kwargs['total_espp']):>14,.2f}")
        print(f"{'401K Loan Gp1':<30} -${abs(kwargs['total_401k_loan_gp1']):>14,.2f}")
        print(f"{'Taxable Off':<30} -${abs(kwargs['total_taxable_off']):>14,.2f}")
        print()
        print(f"{'Total Other Deductions':<30} -${abs(kwargs['total_other_deductions']):>14,.2f}")
        print("-" * 50)
        print()
        print(
            f"{'Net Pay calculated: (Gross Pay - Total Statutory Deductions - Other Deductions)':<50} ${kwargs['calculated_net_pay']:>15,.2f}"
        )
        print(
            f"  Breakdown: ${kwargs['calculated_gross_pay']:>15,.2f} (Gross) - ${kwargs['total_statutory_deductions']:>15,.2f} (Statutory) - ${kwargs['total_other_deductions']:>15,.2f} (Other) = ${kwargs['calculated_net_pay']:>15,.2f}"
        )
        print(f"{'Net Pay from table':<30} ${kwargs['total_net_pay_from_table']:>15,.2f}")
        if kwargs["net_pay_matched"]:
            print(f"{'Matched?':<30} {'Yes':>15}")
        else:
            print(f"{'Matched?':<30} {'No':>15}")
            print(f"{'Difference':<30} ${kwargs['net_pay_difference']:>15,.2f}")
        print()

        # Print transaction count summary
        print("=" * 50)
        print(f"Summary: {kwargs['transaction_count']} payslip(s) considered for {year}")
        print("=" * 50)
