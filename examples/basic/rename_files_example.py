#!/usr/bin/env python3
"""Example: Rename IPay statement files by date."""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from py_statements_parser.core.processor import StatementProcessor
from py_statements_parser.core.config import Config
from py_statements_parser.utils.logging import setup_logging


def main():
    """Example of renaming IPay statement files."""
    
    # Setup logging
    setup_logging(verbose=True)
    
    # Create configuration
    config = Config()
    
    # Initialize processor for IPay
    processor = StatementProcessor("ipay", config)
    
    # Path to statements folder (create if it doesn't exist)
    statements_folder = Path("statements/adp-ipay")
    statements_folder.mkdir(parents=True, exist_ok=True)
    
    print(f"Processing statements in: {statements_folder}")
    print("Make sure you have PDF files in this folder before running.")
    
    # Rename files based on their statement date
    processor.rename_files(statements_folder)
    
    print("File renaming completed!")
    print("Files have been renamed to YYYY-MM-DD format based on their pay date.")


if __name__ == "__main__":
    main() 