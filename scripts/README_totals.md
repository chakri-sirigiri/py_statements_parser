# Generate Totals Script

This directory contains a shell script to generate `.env.totals` files with monthly and yearly totals from the SQLite database.

## Overview

The script queries the `transactions_adp` table in the SQLite database to calculate:
- **Monthly gross pay totals** (G_YYYY_M format)
- **Monthly net pay totals** (N_YYYY_M format)
- **Yearly transaction counts** (T_YYYY format)

## Shell Script (`generate_totals.sh`)

A bash script that uses `sqlite3` command-line tool.

**Requirements:**
- `sqlite3` command-line tool installed
- SQLite database file (`transactions.db` by default)

**Usage:**
```bash
# Use default database path (transactions.db)
./scripts/generate_totals.sh

# Specify custom database path
./scripts/generate_totals.sh /path/to/your/transactions.db
```

**Features:**
- Colored output for better readability
- Error handling for missing database or sqlite3
- Automatic month number formatting (removes leading zeros)
- Summary statistics

## Output Format

The scripts generate a `.env.totals` file with the following format:

```
G_2013_1=123.45
G_2013_2=12312.67
N_2013_1=98.76
N_2013_2=9876.54
T_2013=24
T_2014=26
```

### Key Format Explanation

- **G_YYYY_M**: Gross pay for year YYYY, month M
  - Example: `G_2013_1=123.45` = $123.45 gross pay for January 2013
- **N_YYYY_M**: Net pay for year YYYY, month M
  - Example: `N_2013_1=98.76` = $98.76 net pay for January 2013
- **T_YYYY**: Total transaction count for year YYYY
  - Example: `T_2013=24` = 24 transactions in 2013

### Month Numbering

- Months are numbered 1-12 (no leading zeros)
- January = 1, February = 2, ..., December = 12

## Database Schema

The scripts query the `transactions_adp` table with the following relevant columns:

```sql
CREATE TABLE transactions_adp (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    institution TEXT NOT NULL,
    statement_date DATE NOT NULL,
    gross_pay DECIMAL(10,2),
    net_pay DECIMAL(10,2),
    -- ... other columns
);
```

## Example Usage

### Basic Usage
```bash
# Generate totals from default database
./scripts/generate_totals.sh
```

### Custom Database Path
```bash
# If your database is in a different location
./scripts/generate_totals.sh /path/to/transactions.db
```

## Sample Output

```
Generating totals from database: transactions.db
Querying database for totals...
Processing monthly gross pay totals...
  G_2023_1=6218.00
  G_2023_2=6218.00
  G_2023_3=6218.00
Processing monthly net pay totals...
  N_2023_1=3540.11
  N_2023_2=3540.11
  N_2023_3=3540.11
Processing yearly transaction counts...
  T_2023=36
  T_2024=12
✓ Generated .env.totals successfully!
File contents:
----------------------------------------
G_2023_1=6218.00
G_2023_2=6218.00
G_2023_3=6218.00
N_2023_1=3540.11
N_2023_2=3540.11
N_2023_3=3540.11
T_2023=36
T_2024=12
----------------------------------------
Summary:
  - Monthly gross pay totals: 3 entries
  - Monthly net pay totals: 3 entries
  - Yearly transaction counts: 2 entries
  - Total entries: 8
Done!
```

## Troubleshooting

### Common Issues

1. **Database not found**
   ```
   Error: Database file not found: transactions.db
   ```
   - Ensure the database file exists in the current directory
   - Provide the correct path to your database file

2. **sqlite3 command not found**
   ```
   Error: sqlite3 command not found
   ```
   - Install sqlite3 command-line tool
   - On macOS: `brew install sqlite3`
   - On Ubuntu: `sudo apt-get install sqlite3`

3. **No data found**
   - Ensure your database contains transaction data
   - Check that `gross_pay` and `net_pay` columns have values
   - Verify `statement_date` column contains valid dates

### Debugging

To inspect your database manually:
```bash
sqlite3 transactions.db
.tables
SELECT * FROM transactions_adp LIMIT 5;
.quit
```

## Integration

The generated `.env.totals` file can be:
- Loaded as environment variables in your application
- Used for financial reporting and analysis
- Imported into spreadsheet applications
- Used for tax preparation and year-end summaries

## Contributing

When modifying these scripts:
- Maintain backward compatibility
- Add proper error handling
- Include helpful error messages
- Update this documentation
- Test with sample data
