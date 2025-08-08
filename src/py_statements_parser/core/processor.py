"""Main processor for handling statement operations."""

from pathlib import Path
from typing import List, Dict, Any
from loguru import logger

from .config import Config
from .institutions.base import BaseInstitution
from .institutions.ipay import IPayInstitution
from .institutions.icici import ICICIInstitution
from .institutions.robinhood import RobinhoodInstitution
from .institutions.first_energy import FirstEnergyInstitution
from .institutions.cash_app import CashAppInstitution
from .database import DatabaseManager


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
        self.logger.info(f"Starting file rename and organize process")
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
                
                # Extract date from statement
                statement_date = self.institution.extract_statement_date(pdf_file)
                
                if statement_date:
                    # Create new filename in YYYY-MM-DD format
                    new_filename = f"{statement_date.strftime('%Y-%m-%d')}.pdf"
                    year = statement_date.year
                    
                    # Get target folder for this institution and year
                    target_folder = self.config.get_target_folder(self.financial_institution, year)
                    new_filepath = target_folder / new_filename
                    
                    # Check if file already exists in target location
                    if new_filepath.exists():
                        self.logger.warning(f"File {new_filename} already exists in {target_folder}, skipping {pdf_file.name}")
                        continue
                    
                    # Move the file to the target location
                    pdf_file.rename(new_filepath)
                    self.logger.info(f"Moved {pdf_file.name} to {new_filepath}")
                else:
                    self.logger.warning(f"Could not extract date from {pdf_file.name}")
                    
            except Exception as e:
                self.logger.error(f"Error processing {pdf_file.name}: {str(e)}")
        
        self.logger.info("File rename and organize process completed")
    
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
        
        self.logger.info(f"Found {len(pdf_files)} PDF files to extract transactions from")
        
        for pdf_file in pdf_files:
            try:
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
        
        self.logger.info(f"Found {len(pdf_files)} PDF files to extract transactions from")
        
        for pdf_file in pdf_files:
            try:
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