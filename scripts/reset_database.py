#!/usr/bin/env python3
"""
Database reset script to recreate the transactions_adp table with all new columns.
This script will drop the existing table and recreate it with the updated schema.
"""

import sqlite3
import sys
from pathlib import Path


def reset_database(db_path: str) -> bool:
    """Reset the database by dropping and recreating the transactions_adp table."""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            print(f"Resetting database: {db_path}")

            # Drop the existing table if it exists
            cursor.execute("DROP TABLE IF EXISTS transactions_adp")
            print("Dropped existing transactions_adp table")

            # Create the new table with all columns
            cursor.execute("""
                CREATE TABLE transactions_adp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    institution TEXT NOT NULL,
                    statement_date DATE NOT NULL,
                    source_file TEXT,
                    regular_pay DECIMAL(10,2),
                    bonus DECIMAL(10,2),
                    other_income DECIMAL(10,2),
                    gross_pay DECIMAL(10,2),
                    federal_income_tax DECIMAL(10,2),
                    social_security_tax DECIMAL(10,2),
                    medicare_tax DECIMAL(10,2),
                    state_income_tax DECIMAL(10,2),
                    local_income_tax DECIMAL(10,2),
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
                    net_pay DECIMAL(10,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("Created new transactions_adp table with updated schema")

            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_institution_date
                ON transactions_adp(institution, statement_date)
            """)
            print("Created index on institution and statement_date")

            conn.commit()
            print(f"Successfully reset database: {db_path}")
            return True

    except Exception as e:
        print(f"Error resetting database {db_path}: {e}")
        return False


def main():
    """Main function."""
    # Default database path
    db_path = "transactions.db"

    print("Database Reset Tool")
    print("=" * 50)
    print("This will DELETE ALL EXISTING DATA and recreate the database with the new schema.")
    print("Make sure you have backups if needed.")
    print()

    # Check if database exists
    if Path(db_path).exists():
        print(f"Found existing database: {db_path}")
        print("This will be completely reset with the new schema.")
    else:
        print(f"Database {db_path} not found. Creating new database with updated schema.")

    print()
    response = input("Do you want to continue? (yes/no): ").lower().strip()

    if response in ["yes", "y"]:
        success = reset_database(db_path)
        if success:
            print("\n✅ Database reset completed successfully!")
            print("You can now run the extraction process to populate the database with fresh data.")
            return True
        else:
            print("\n❌ Database reset failed!")
            return False
    else:
        print("\nOperation cancelled.")
        return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
