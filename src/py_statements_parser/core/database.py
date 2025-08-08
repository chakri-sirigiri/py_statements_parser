"""Database management for Py Statements Parser."""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from .config import DatabaseConfig


class DatabaseManager:
    """Manages database operations for storing and retrieving transaction data."""
    
    def __init__(self, config: DatabaseConfig):
        """Initialize database manager with configuration."""
        self.config = config
        self.logger = logger.bind(name="DatabaseManager")
        
        # Set up database path
        if config.type == "sqlite":
            self.db_path = Path(config.path or "transactions.db")
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            raise NotImplementedError(f"Database type {config.type} not yet supported")
        
        # Initialize database
        self._init_database()
        self.logger.info(f"Initialized database at {self.db_path}")
    
    def _init_database(self) -> None:
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    institution TEXT NOT NULL,
                    statement_date DATE NOT NULL,
                    pay_period TEXT,
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
                    vol_acc_40_20 DECIMAL(10,2),
                    vol_child_life DECIMAL(10,2),
                    vol_spousal_life DECIMAL(10,2),
                    k401_pretax DECIMAL(10,2),
                    net_pay DECIMAL(10,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_institution_date 
                ON transactions(institution, statement_date)
            """)
            
            conn.commit()
    
    def store_transactions(self, transactions: List[Dict[str, Any]]) -> None:
        """Store transactions in the database."""
        if not transactions:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for transaction in transactions:
                # Check if transaction already exists
                cursor.execute("""
                    SELECT id FROM transactions 
                    WHERE institution = ? AND statement_date = ?
                """, (transaction["institution"], transaction["statement_date"]))
                
                if cursor.fetchone():
                    self.logger.warning(f"Transaction for {transaction['institution']} on {transaction['statement_date']} already exists")
                    continue
                
                # Insert new transaction
                cursor.execute("""
                    INSERT INTO transactions (
                        institution, statement_date, pay_period, gross_pay,
                        federal_income_tax, social_security_tax, medicare_tax,
                        state_income_tax, local_income_tax, hsa_plan,
                        illness_plan, legal, life_insurance, pretax_dental,
                        pretax_medical, pretax_vision, vol_acc_40_20,
                        vol_child_life, vol_spousal_life, k401_pretax, net_pay
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    transaction["institution"],
                    transaction["statement_date"],
                    transaction.get("pay_period"),
                    transaction.get("gross_pay"),
                    transaction.get("federal_income_tax"),
                    transaction.get("social_security_tax"),
                    transaction.get("medicare_tax"),
                    transaction.get("state_income_tax"),
                    transaction.get("local_income_tax"),
                    transaction.get("hsa_plan"),
                    transaction.get("illness_plan"),
                    transaction.get("legal"),
                    transaction.get("life_insurance"),
                    transaction.get("pretax_dental"),
                    transaction.get("pretax_medical"),
                    transaction.get("pretax_vision"),
                    transaction.get("vol_acc_40_20"),
                    transaction.get("vol_child_life"),
                    transaction.get("vol_spousal_life"),
                    transaction.get("k401_pretax"),
                    transaction.get("net_pay"),
                ))
            
            conn.commit()
            self.logger.info(f"Stored {len(transactions)} transactions")
    
    def get_all_transactions(self, institution: str) -> List[Dict[str, Any]]:
        """Get all transactions for a specific institution."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM transactions 
                WHERE institution = ? 
                ORDER BY statement_date DESC
            """, (institution,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_transactions_by_date_range(
        self, 
        institution: str, 
        start_date: str, 
        end_date: str
    ) -> List[Dict[str, Any]]:
        """Get transactions within a date range."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM transactions 
                WHERE institution = ? AND statement_date BETWEEN ? AND ?
                ORDER BY statement_date DESC
            """, (institution, start_date, end_date))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def delete_transactions(self, institution: str, statement_date: Optional[str] = None) -> int:
        """Delete transactions for an institution, optionally for a specific date."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if statement_date:
                cursor.execute("""
                    DELETE FROM transactions 
                    WHERE institution = ? AND statement_date = ?
                """, (institution, statement_date))
            else:
                cursor.execute("""
                    DELETE FROM transactions 
                    WHERE institution = ?
                """, (institution,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            self.logger.info(f"Deleted {deleted_count} transactions for {institution}")
            return deleted_count 