# iPay Statements Parser

A comprehensive tool for processing and analyzing iPay pay statements. This tool can rename, organize, extract, and reconcile pay statement data with powerful YTD reconciliation capabilities.

## Features

### 📁 File Organization
- **Rename and organize** statement files by year and payment type
- **Automatic date extraction** from PDF statements
- **Smart payment type detection** based on input filename conventions:
  - **Regular**: Any file not containing `bonus` or `ytd` in filename
  - **Bonus**: Files containing `bonus` anywhere in filename
  - **Year-end summary**: Files containing `ytd` anywhere in filename (skipped during transaction extraction)
- **Structured folder organization** by institution and year

### 📊 Data Extraction
- **Extract transaction data** from PDF pay statements
- **Store in SQLite database** for analysis and reconciliation
- **Support for all pay components**:
  - **Earnings**: Regular pay, bonus/performance, vacation pay, other income (Cola, Retro Cola, Contribution, Award, Skillpay Allow) - other income skipped for bonus and vacation paychecks
  - **Statutory Deductions**: Federal, state (OH State Income Tax, NC State Income Tax), and local taxes (including Cleveland Income Tax, Brooklyn Income Tax), Social Security and Medicare
  - **Other Deductions**: Health benefits (HSA, medical, dental, vision, dep care), life insurance, 401K contributions, ESPP, 401K loans
  - **Net Pay**: Direct extraction or fallback to checking account totals when net pay is 0 (supports multiple checking accounts with current period vs YTD logic)
  - Once Data is extracted, the tool will consider the following logic. if there is a mismatch, the tool throws exemption and exit.
    - for all regular paychecks,
      Net pay = Gross pay - statuary deductions - other deductions
      Gross pay = Regular pay + other income (Cola, Retro Cola, Contribution, Award, Skillpay Allow)
      statuary deductions = Federal, state (OH State Income Tax, NC State Income Tax), and local taxes (including Cleveland Income Tax, Brooklyn Income Tax), Social Security and Medicare
      other deductions = Health benefits (HSA, medical, dental, vision, dep care), life insurance, 401K contributions, ESPP, 401K loans
    - for all bonus paychecks,
      Net pay = Bonus - statuary deductions
      Gross pay = Bonus
      statuary deductions = Federal, state (OH State Income Tax, NC State Income Tax), and local taxes (including Cleveland Income Tax, Brooklyn Income Tax), Social Security and Medicare
      other deductions = Espp only if present.
    - for all vacation paychecks,
      Net pay = Vacation - statuary deductions - 401K pretax (if present)
      Gross pay = Vacation (mapped to other_income)
      statuary deductions = Federal, state (OH State Income Tax, NC State Income Tax), and local taxes (including Cleveland Income Tax, Brooklyn Income Tax), Social Security and Medicare
      other deductions = 401K pretax only if present.
    - for all other paychecks (ytd summary), no data is extracted. no checks are done.
  - almost all paychecks have a line with description followed by two values. the first value is the amount for that paycheck, the second value is the ytd amount for that paycheck.
    - if the both first and second values are present, then consider the first value as the amount for that paycheck, and the second value as the ytd amount for that paycheck.
    - if only one value is present, then consider the value as the amount for that paycheck is zero, and the value found is the ytd amount for that income/deduction.

### 📈 YTD Reconciliation
- **Year-to-date transaction reconciliation** with detailed breakdowns
- **Earnings verification** (regular pay + bonus vs gross pay)
- **Deduction categorization** into statutory and other deductions
- **Net pay validation** with calculated vs stored comparisons
- **Comprehensive reporting** for tax and financial planning

### 📋 Additional Features
- **Excel report generation** with all transaction data
- **Quicken integration** for financial software import
- **Comprehensive logging** for troubleshooting
- **Configuration management** for different environments

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd py_statements_parser
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Set up configuration**:
   ```bash
   cp config.yaml.example config.yaml
   cp env.example .env
   # Edit config.yaml and .env with your settings
   ```

## Configuration

### Environment Variables (.env)
```bash
# Required folders
INPUT_STATEMENTS_FOLDER=/path/to/unsorted/statements
TARGET_STATEMENTS_FOLDER=/path/to/organized/statements

# Database configuration
DATABASE_PATH=transactions.db

# Quicken integration (optional)
QUICKEN_ENABLED=false
QUICKEN_PATH=/Applications/Quicken.app
```

### Configuration File (config.yaml)
```yaml
database:
  type: sqlite
  path: transactions.db

institutions:
  ipay:
    name: "FirstEnergy iPay"
    statement_pattern: "*.pdf"

quicken:
  enabled: false
  path: "/Applications/Quicken.app"
```

## Usage

### Basic Commands

#### 1. Rename and Organize Files
```bash
uv run python -m src.py_statements_parser.main \
  --financial-institution ipay \
  --feature rename-file \
  --input-folder /path/to/unsorted/statements
```

#### 2. Extract Transactions
```bash
uv run python -m src.py_statements_parser.main \
  --financial-institution ipay \
  --feature extract-transactions \
  --input-folder /path/to/unsorted/statements
```

#### 3. Generate Excel Report
```bash
uv run python -m src.py_statements_parser.main \
  --financial-institution ipay \
  --feature generate-excel \
  --input-folder /path/to/unsorted/statements
```

### YTD Reconciliation

The YTD reconciliation feature is one of the most powerful tools for verifying your pay statement accuracy and preparing for tax season.

#### YTD Reconciliation Formats

The reconciliation feature supports two formats for the `--year` parameter:

**Full Year Reconciliation**:
- Format: `YYYY` (e.g., `2024`)
- Reconciles all transactions for the entire year
- Example: `--year 2024`

**Month-Year Reconciliation**:
- Format: `MM-YYYY` (e.g., `06-2024`)
- Reconciles transactions up to and including the specified month
- Useful for mid-year reconciliations or partial year analysis
- Example: `--year 06-2024` (reconciles January through June 2024)

#### Basic YTD Reconciliation
```bash
# Full year reconciliation
uv run python -m src.py_statements_parser.main \
  --financial-institution ipay \
  --feature reconcile-ytd-transactions \
  --year 2024

# Month-year reconciliation (up to specific month)
uv run python -m src.py_statements_parser.main \
  --financial-institution ipay \
  --feature reconcile-ytd-transactions \
  --year 06-2024
```

#### Example Output (Matched)
```
Sum of Earnings YTD for 2024 are:
==================================================
Regular Pay                           $    6,218.00
Bonus                                 $        0.00
Other Income                          $        0.00
Gross Pay (sum of all earlier items)  $    6,218.00
Gross Pay from table                  $    6,218.00
Matched?                              Yes

Deductions:
==================================================
Deductions Statutory
--------------------------------------------------
Federal Income Tax                    $   -983.91
Social Security Tax                   $   -356.05
Medicare Tax                          $    -83.27
State Income Tax                      $   -155.54
Local Income Tax                      $   -143.57

Total Statutory Deductions            $ -1,722.34
--------------------------------------------------

Other Deductions
--------------------------------------------------
HSA Plan                              $   -304.00
Illness Plan                          $     -6.80
Legal                                 $     -8.25
Life Insurance                        $     -8.78
Pretax Dental                         $    -42.76
Pretax Medical                        $   -132.79
Pretax Vision                         $     -8.09
Vol Acc 40/20                         $     -7.97
Vol Child Life                        $     -0.48
Vol Spousal Life                      $     -0.37
401K Pretax                           $   -435.26
Taxable Off                           $      0.00

Total Other Deductions                $   -955.55
--------------------------------------------------

Net Pay calculated: (Gross Pay + Total Statutory Deductions + Other Deductions) $    3,540.11
Net Pay from table                    $    3,540.11
Matched?                              Yes
```

#### Example Output (Mismatch Detected)
```
Sum of Earnings YTD for 2024 are:
==================================================
Regular Pay                           $    6,218.00
Bonus                                 $        0.00
Gross Pay (sum of all earlier items)  $    6,218.00
Gross Pay from table                  $    6,200.00
Matched?                              No
Difference                            $       18.00

Deductions:
==================================================
Deductions Statutory
--------------------------------------------------
Federal Income Tax                    $   -983.91
Social Security Tax                   $   -356.05
Medicare Tax                          $    -83.27
State Income Tax                      $   -155.54
Local Income Tax                      $   -143.57

Total Statutory Deductions            $ -1,722.34
--------------------------------------------------

Other Deductions
--------------------------------------------------
HSA Plan                              $   -304.00
Illness Plan                          $     -6.80
Legal                                 $     -8.25
Life Insurance                        $     -8.78
Pretax Dental                         $    -42.76
Pretax Medical                        $   -132.79
Pretax Vision                         $     -8.09
Vol Acc 40/20/20/10                   $     -7.97
Vol Child Life                        $     -0.48
Vol Spousal Life                      $     -0.37
401K Pretax                           $   -435.26
Taxable Off                           $      0.00

Total Other Deductions                $   -955.55
--------------------------------------------------

Net Pay calculated: (Gross Pay + Total Statutory Deductions + Other Deductions) $    3,540.11
Net Pay from table                    $    3,522.11
Matched?                              No
Difference                            $       18.00
```

#### What the YTD Reconciliation Does

1. **Earnings Verification**:
   - Sums all regular pay and bonus amounts for the year
   - Compares with the total gross pay from statements
   - Identifies any discrepancies in earnings calculations

2. **Deduction Categorization**:
   - **Statutory Deductions**: Taxes (federal, state, local, social security, medicare)
   - **Other Deductions**: Benefits, insurance, 401K, etc.

3. **Net Pay Validation**:
   - Calculates net pay as: Gross Pay + Statutory Deductions + Other Deductions (since deductions are stored as negative values)
   - Compares with stored net pay values
   - Highlights any calculation mismatches

4. **Tax Planning Support**:
   - Provides year-to-date totals for tax preparation
   - Helps verify W-2 accuracy
   - Identifies potential payroll errors

### Advanced Usage

#### Extract from Already Organized Files
```bash
uv run python -m src.py_statements_parser.main \
  --financial-institution ipay \
  --feature extract-from-organized
```

#### Quicken Integration
```bash
uv run python -m src.py_statements_parser.main \
  --financial-institution ipay \
  --feature enter-to-quicken
```

#### Verbose Logging
```bash
uv run python -m src.py_statements_parser.main \
  --financial-institution ipay \
  --feature reconcile-ytd-transactions \
  --year 2024 \
  --verbose
```

## Database Schema

The tool uses SQLite to store transaction data with the following structure:

```sql
CREATE TABLE transactions_adp (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    institution TEXT NOT NULL,
    statement_date DATE NOT NULL,
    source_file TEXT,

    -- Earnings
    regular_pay DECIMAL(10,2),
    bonus DECIMAL(10,2),
    other_income DECIMAL(10,2),
    gross_pay DECIMAL(10,2),

    -- Statutory Deductions
    federal_income_tax DECIMAL(10,2),
    social_security_tax DECIMAL(10,2),
    medicare_tax DECIMAL(10,2),
    state_income_tax DECIMAL(10,2),
    local_income_tax DECIMAL(10,2),

    -- Other Deductions
    hsa_plan DECIMAL(10,2),
    illness_plan DECIMAL(10,2),
    legal DECIMAL(10,2),
    life_insurance DECIMAL(10,2),
    pretax_dental DECIMAL(10,2),
    pretax_medical DECIMAL(10,2),
    pretax_vision DECIMAL(10,2),
    dep_care DECIMAL(10,2),
    vol_acc_40_20 DECIMAL(10,2),
    vol_child_life DECIMAL(10,2),
    vol_spousal_life DECIMAL(10,2),
    k401_pretax DECIMAL(10,2),
    espp DECIMAL(10,2),
    k401_loan_gp1 DECIMAL(10,2),
    taxable_off DECIMAL(10,2),

    -- Net Pay
    net_pay DECIMAL(10,2),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## File Organization

### Payment Type Detection Logic

The tool automatically determines file types based on input filename conventions and PDF content:

| File Type | Detection Method | Output Filename |
|-----------|------------------|-----------------|
| **Regular** | No `bonus` or `ytd` in filename or content | `2024-01-15-regular.pdf` |
| **Bonus** | Contains `bonus` in filename OR PDF content shows bonus pattern | `2024-02-15-bonus.pdf` |
| **Year-end Summary** | Contains `ytd` anywhere in filename | `2024-12-31-ytd-summary.pdf` |

**Note**: Bonus detection prioritizes filename over PDF content. If filename contains "bonus", it's treated as a bonus paycheck regardless of PDF content.

**Note**: Vacation detection prioritizes filename over PDF content. If filename contains "vacation", it's treated as a vacation paycheck regardless of PDF content.

**Note**: YTD files are renamed but skipped during transaction extraction since they contain only summary data.

After processing, files are organized as follows:

```
TARGET_STATEMENTS_FOLDER/
└── ipay/
    ├── 2024/
    │   ├── 2024-01-15-regular.pdf
    │   ├── 2024-01-31-regular.pdf
    │   ├── 2024-02-15-bonus.pdf
    │   └── 2024-12-31-ye-summary.pdf
    ├── 2023/
    │   ├── 2023-12-15-regular.pdf
    │   └── 2023-12-31-regular.pdf
    └── transactions.xlsx
```

## Troubleshooting

### Common Issues

1. **No transactions found for year X**:
   - Ensure you've run `extract-transactions` first
   - Check that PDF files are in the correct format
   - Verify the year parameter matches your data

2. **Gross pay doesn't match**:
   - Check for additional earnings components not captured
   - Verify PDF parsing accuracy
   - Review statement format changes

3. **Net pay calculation mismatch**:
   - Look for missing deduction categories
   - Check for rounding differences
   - Verify all deduction fields are populated
   - Check if net pay is split across multiple checking accounts

4. **Net pay shows as 0**:
   - System automatically looks for checking account entries
   - Supports multiple checking accounts (Checking1, Checking2, etc.)
   - **Current Period vs YTD Logic**:
     - **Two amounts**: `Checking2 1 040 30 6 040 30` → Uses first amount (1,040.30) as current period
     - **One amount**: `Checking3 4 489 62` → Uses amount (4,489.62) as current period (YTD only means current period is 0)
   - Sums all checking account current period amounts to calculate total net pay

### Debug Mode

Enable verbose logging to see detailed processing information:

```bash
uv run python -m src.py_statements_parser.main \
  --financial-institution ipay \
  --feature reconcile-ytd-transactions \
  --year 2024 \
  --verbose
```

### Database Inspection

You can inspect the database directly:

```bash
sqlite3 transactions.db
.tables
SELECT * FROM transactions_adp WHERE institution = 'ipay' AND strftime('%Y', statement_date) = '2024';
```

## Best Practices

1. **Regular Reconciliation**: Run YTD reconciliation monthly to catch errors early
2. **Backup Data**: Keep backups of your organized statements and database
3. **Tax Preparation**: Use YTD reconciliation data for accurate tax filing
4. **Error Investigation**: Investigate any mismatches found during reconciliation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs with verbose mode
3. Open an issue on GitHub with detailed information
