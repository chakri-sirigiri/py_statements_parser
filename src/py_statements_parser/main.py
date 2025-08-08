"""Main CLI application for Py Statements Parser."""

import typer
from pathlib import Path
from typing import Optional

from .core.processor import StatementProcessor
from .core.config import Config
from .utils.logging import setup_logging

app = typer.Typer(
    name="py-statements-parser",
    help="Process statements from various financial institutions",
    add_completion=False,
)


@app.command()
def main(
    financial_institution: str = typer.Option(
        ...,
        "--financial-institution",
        "-fi",
        help="Financial institution to process (ipay, icici, robinhood, first-energy, cash-app)",
    ),
    feature: str = typer.Option(
        ...,
        "--feature",
        "-f",
        help="Feature to execute (rename-file, extract-transactions, extract-from-organized, generate-excel, enter-to-quicken)",
    ),
    input_folder: Optional[Path] = typer.Option(
        None,
        "--input-folder",
        "-if",
        help="Path to folder containing unsorted statements (overrides INPUT_STATEMENTS_FOLDER env var)",
    ),
    target_folder: Optional[Path] = typer.Option(
        None,
        "--target-folder", 
        "-tf",
        help="Path to folder where organized statements will be saved (overrides TARGET_STATEMENTS_FOLDER env var)",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
) -> None:
    """Process statements from various financial institutions."""
    
    # Setup logging
    setup_logging(verbose=verbose)
    
    # Load configuration
    config = Config.from_file(config_file) if config_file else Config()
    
    # Override environment variables with command line arguments if provided
    if input_folder:
        config.input_statements_folder = str(input_folder)
    if target_folder:
        config.target_statements_folder = str(target_folder)
    
    # Validate inputs
    if feature not in ["rename-file", "extract-transactions", "extract-from-organized", "generate-excel", "enter-to-quicken"]:
        typer.echo(f"Error: Invalid feature '{feature}'. Must be one of: rename-file, extract-transactions, extract-from-organized, generate-excel, enter-to-quicken")
        raise typer.Exit(1)
    
    if financial_institution not in ["ipay", "icici", "robinhood", "first-energy", "cash-app"]:
        typer.echo(f"Error: Invalid financial institution '{financial_institution}'. Must be one of: ipay, icici, robinhood, first-energy, cash-app")
        raise typer.Exit(1)
    
    # Validate input folder
    if feature in ["rename-file", "extract-transactions", "generate-excel"] and not config.input_statements_folder:
        typer.echo(f"Error: Input folder is required for feature '{feature}'")
        typer.echo("Please provide --input-folder or set INPUT_STATEMENTS_FOLDER environment variable")
        raise typer.Exit(1)
    
    # Validate target folder for features that need it
    if feature in ["rename-file", "extract-from-organized"] and not config.target_statements_folder:
        typer.echo("Error: Target folder is required for this feature")
        typer.echo("Please provide --target-folder or set TARGET_STATEMENTS_FOLDER environment variable")
        typer.echo("You can do this in one of two ways:")
        typer.echo("1. Set it in a .env file: TARGET_STATEMENTS_FOLDER=/path/to/your/organized/statements")
        typer.echo("2. Export it in your shell: export TARGET_STATEMENTS_FOLDER=/path/to/your/organized/statements")
        typer.echo("Example: export TARGET_STATEMENTS_FOLDER=/Users/username/Documents/Financial/Statements")
        raise typer.Exit(1)
    
    input_path = Path(config.input_statements_folder).expanduser() if config.input_statements_folder else None
    if input_path and not input_path.exists():
        typer.echo(f"Error: Input folder '{input_path}' does not exist")
        raise typer.Exit(1)
    

    
    try:
        # Initialize processor
        processor = StatementProcessor(
            financial_institution=financial_institution,
            config=config,
        )
        
        # Execute feature
        if feature == "rename-file":
            processor.rename_files(input_path)
        elif feature == "extract-transactions":
            processor.extract_transactions(input_path)
        elif feature == "extract-from-organized":
            processor.extract_transactions_from_organized()
        elif feature == "generate-excel":
            processor.generate_excel(input_path)
        elif feature == "enter-to-quicken":
            processor.enter_to_quicken()
            
        typer.echo(f"Successfully completed {feature} for {financial_institution}")
        
    except Exception as e:
        typer.echo(f"Error: {str(e)}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app() 