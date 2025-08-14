# Py Statements Parser

A Python application to process statements from various financial institutions, extract transaction data, and manage financial records.

## Features

- Process statements from various financial institutions
- Rename statement files to the date of the statement (YYYY-MM-DD format)
- Extract transactions from statements using PDF text extraction
- Store transaction data in a local SQLite database
- Generate Excel files with extracted transactions
- Integration with Quicken application (planned)
- Comprehensive logging and error handling

## Supported Financial Institutions

- **ADP IPay Statements** - Fully implemented
- ICICI Bank Statements - Placeholder
- Robinhood Statements - Placeholder
- First Energy Statements - Placeholder
- Cash App Statements - Placeholder

## Installation

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Quick Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd py_statements_parser
```

2. Run the setup script:
```bash
python scripts/setup.py
```

Or manually install dependencies:
```bash
uv sync
```

## Usage

### Command Line Interface

The application provides a CLI with the following structure:

```bash
python main.py --financial-institution <institution> --feature <feature> [--input-folder <path>] [--target-folder <path>]
```

#### Arguments

- `--financial-institution` (`-fi`): Financial institution to process
  - `ipay` - ADP IPay
  - `icici` - ICICI Bank
  - `robinhood` - Robinhood
  - `first-energy` - First Energy
  - `cash-app` - Cash App

- `--feature` (`-f`): Feature to execute
  - `rename-file` - Rename and organize statement files by year
  - `extract-transactions` - Extract and store transactions (includes renaming first)
  - `reconcile-ytd-transactions` - Reconcile YTD transactions (YYYY or MM-YYYY format)
  - `extract-from-organized` - Extract transactions from already organized files
  - `generate-excel` - Generate Excel file with transactions
  - `enter-to-quicken` - Enter transactions into Quicken

- `--input-folder` (`-if`): Path to folder containing unsorted statements (overrides INPUT_STATEMENTS_FOLDER env var)
- `--target-folder` (`-tf`): Path to folder where organized statements will be saved (overrides TARGET_STATEMENTS_FOLDER env var)
- `--year` (`-y`): Year for YTD reconciliation (YYYY or MM-YYYY format, required for reconcile-ytd-transactions feature)
- `--config` (`-c`): Path to configuration file (optional)
- `--verbose` (`-v`): Enable verbose logging

#### Environment Variables

- `INPUT_STATEMENTS_FOLDER`: Input folder containing unsorted statements
- `TARGET_STATEMENTS_FOLDER`: Target folder for organized statements (required for rename-file feature)
  - Files will be organized by institution and year: `{TARGET_STATEMENTS_FOLDER}/{institution}/{year}/YYYY-MM-DD.pdf`

the statements are not only renamed, but also moved and organized by year, into the statements/YYYY folder, for each financial institution. the path of the target root folder is specified in .env file. the target folder is created if it doesn't exist.
example:
{statements-folder}/Statement for Jul 31, 2025.pdf -> {STATEMENTS_FOLDER}/adp/2025/2025-07-31.pdf
{statements-folder}/Statement for Aug 31, 2025.pdf -> {STATEMENTS_FOLDER}/adp/2025/2025-08-31.pdf
{statements-folder}/ICICI Bank Statement for Aug 31, 2025.pdf -> {STATEMENTS_FOLDER}/icici/2025/2025-08-31.pdf




#### Examples

```bash
# Set environment variables (optional - can also use command line arguments)
export INPUT_STATEMENTS_FOLDER=/path/to/your/unsorted/statements
export TARGET_STATEMENTS_FOLDER=/path/to/your/organized/statements

# Rename and organize IPay statement files by year (using env vars)
python main.py --financial-institution ipay --feature rename-file

# Rename and organize IPay statement files by year (using command line args)
python main.py --financial-institution ipay --feature rename-file --input-folder statements/adp-ipay --target-folder /path/to/organized

# Extract transactions from IPay statements (includes renaming first)
python main.py --financial-institution ipay --feature extract-transactions --input-folder statements/adp-ipay

# Extract transactions from already organized files
python main.py --financial-institution ipay --feature extract-from-organized

# Generate Excel file with extracted transactions
python main.py --financial-institution ipay --feature generate-excel --input-folder statements/adp-ipay

# Enter transactions into Quicken (when implemented)
python main.py --financial-institution ipay --feature enter-to-quicken

# Reconcile YTD transactions for 2025
uv run python main.py -fi ipay -f reconcile-ytd-transactions -y 2025

# Reconcile YTD transactions up to June 2025
uv run python main.py -fi ipay -f reconcile-ytd-transactions -y 06-2025
```

**File Organization Example:**
```
Source: {INPUT_STATEMENTS_FOLDER}/Statement for Jul 31, 2025.pdf
Target: {TARGET_STATEMENTS_FOLDER}/ipay/2025/2025-07-31-regular.pdf

Source: {INPUT_STATEMENTS_FOLDER}/Statement for Aug 31, 2025.pdf
Target: {TARGET_STATEMENTS_FOLDER}/ipay/2025/2025-08-31-regular.pdf

Source: {INPUT_STATEMENTS_FOLDER}/ICICI Bank Statement for Aug 31, 2025.pdf
Target: {TARGET_STATEMENTS_FOLDER}/icici/2025/2025-08-31.pdf

Source: {INPUT_STATEMENTS_FOLDER}/Year End Summary 2025.pdf
Target: {TARGET_STATEMENTS_FOLDER}/ipay/2025/2025-12-31-ye-summary.pdf
```

**Note**: Files are automatically categorized based on input filename conventions:
- **Regular**: Any file not containing `bonus` or `ytd` → `-regular.pdf`
- **Bonus**: Files containing `bonus` anywhere in filename → `-bonus.pdf`
- **Year-end summary**: Files containing `ytd` anywhere in filename → `-ye-summary.pdf` (skipped during transaction extraction)

### Workflow

1. **Initial Setup**: Place unsorted statement files in your input folder
2. **Organize Files**: Use `rename-file` to organize files by institution and year
3. **Extract Data**: Use `extract-transactions` (includes renaming) or `extract-from-organized` (for already organized files)
4. **Generate Reports**: Use `generate-excel` to create Excel reports from extracted data

**Note**: The `extract-transactions` feature automatically includes the renaming step, so files are moved from input to target folder during processing. If you've already organized files, use `extract-from-organized` instead.

### ADP IPay Statement Processing

The IPay processor extracts the following information from statements:

- **Pay Date**: Used to rename files to YYYY-MM-DD format
- **Regular Pay**: Regular salary amount from "Regular" line
- **Bonus**: Bonus amount from "Bonus" line (if present)
- **Vacation**: Vacation pay amount from "Vacation" line (mapped to other_income)
- **Gross Pay**: Calculated as Regular Pay + Bonus
- **Federal Income Tax**: Federal tax deductions
- **Social Security Tax**: Social security contributions
- **Medicare Tax**: Medicare contributions
- **OH State Income Tax**: Ohio state tax
- **Brooklyn Income Tax**: Local tax deductions
- **HAS Plan**: Health Savings Account contributions
- **Illness Plan**: Illness plan deductions
- **Legal**: Legal plan contributions
- **Life Insurance**: Life insurance premiums
- **Pretax Dental**: Dental plan contributions

**📖 For detailed iPay documentation including YTD reconciliation features, see [README_ipay.md](README_ipay.md)**
- **Pretax Medical**: Medical plan contributions
- **Pretax Vision**: Vision plan contributions
- **Vol Acc 40/20/20/10**: Voluntary accident insurance (supports both 40/20 and 20/10 variations)
- **Vol Child Life**: Voluntary child life insurance
- **Vol Spousal Life**: Voluntary spousal life insurance
- **401K Pretax**: 401(k) contributions
- **Net Pay**: Final net pay amount

### Configuration

Copy the example configuration and customize as needed:

```bash
cp config.yaml.example config.yaml
```

Key configuration options:
- Database settings (SQLite by default)
- Logging configuration
- Quicken integration settings
- Institution-specific settings

## Project Structure

```
py_statements_parser/
├── src/py_statements_parser/
│   ├── core/                    # Core processing logic
│   │   ├── processor.py         # Main processor
│   │   ├── config.py           # Configuration management
│   │   ├── database.py         # Database operations
│   │   └── institutions/       # Institution handlers
│   ├── utils/                  # Utility modules
│   └── main.py                 # CLI application
├── examples/                   # Usage examples
├── tests/                     # Test suite
├── scripts/                   # Development scripts
├── data/                      # Database files
├── logs/                      # Log files
├── statements/                # Statement folders
└── main.py                    # Entry point
```

## Development

### Running Tests

```bash
uv run pytest
```

### Code Quality

```bash
uv run ruff check --fix
uv run ruff format
```

### Adding New Institutions

1. Create a new handler in `src/py_statements_parser/core/institutions/`
2. Inherit from `BaseInstitution`
3. Implement the required methods
4. Add the handler to the processor mapping



## License

[Add your license information here]
# Test comment
# Another test comment
# Final test comment
# test comment 2
# Test comment
# Another test comment
