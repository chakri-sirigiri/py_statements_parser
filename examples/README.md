# Py Statements Parser Examples

This directory contains examples demonstrating how to use the Py Statements Parser.

## Basic Examples

### rename_files_example.py

Demonstrates how to rename IPay statement files based on their pay date.

```bash
# Run the example
python examples/basic/rename_files_example.py
```

This example:
1. Sets up logging and configuration
2. Initializes the IPay processor
3. Processes PDF files in the `statements/adp-ipay` folder
4. Renames files to YYYY-MM-DD format based on the pay date

## Usage

1. Place your PDF statement files in the appropriate folder (e.g., `statements/adp-ipay/`)
2. Run the example script
3. Check the results in the same folder

## Requirements

- PDF files must be valid ADP IPay statements
- Files should contain a "Pay Date" field that can be extracted
- The application will create necessary directories automatically
