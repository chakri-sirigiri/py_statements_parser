#!/usr/bin/env python3
"""Demonstration of the rename and organize functionality."""

import os
from pathlib import Path

def demonstrate_file_organization():
    """Demonstrate how files will be organized."""
    
    print("Py Statements Parser - File Organization Demo")
    print("=" * 50)
    
    # Example environment variable
    statements_folder = "/Users/username/Documents/Financial/Statements"
    os.environ["STATEMENTS_FOLDER"] = statements_folder
    
    print(f"STATEMENTS_FOLDER: {statements_folder}")
    print()
    
    # Example file transformations
    examples = [
        {
            "source": "statements/adp-ipay/Statement for Jul 31, 2025.pdf",
            "target": f"{statements_folder}/ipay/2025/2025-07-31.pdf",
            "institution": "ipay",
            "year": 2025
        },
        {
            "source": "statements/adp-ipay/Statement for Aug 31, 2025.pdf", 
            "target": f"{statements_folder}/ipay/2025/2025-08-31.pdf",
            "institution": "ipay",
            "year": 2025
        },
        {
            "source": "statements/icici/ICICI Bank Statement for Aug 31, 2025.pdf",
            "target": f"{statements_folder}/icici/2025/2025-08-31.pdf",
            "institution": "icici", 
            "year": 2025
        },
        {
            "source": "statements/adp-ipay/Statement for Sep 30, 2024.pdf",
            "target": f"{statements_folder}/ipay/2024/2024-09-30.pdf",
            "institution": "ipay",
            "year": 2024
        }
    ]
    
    print("File Organization Examples:")
    print("-" * 30)
    
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example['source']}")
        print(f"   → {example['target']}")
        print(f"   Institution: {example['institution']}")
        print(f"   Year: {example['year']}")
        print()
    
    # Show directory structure
    print("Resulting Directory Structure:")
    print("-" * 30)
    print(f"{statements_folder}/")
    print("├── ipay/")
    print("│   ├── 2024/")
    print("│   │   └── 2024-09-30.pdf")
    print("│   └── 2025/")
    print("│       ├── 2025-07-31.pdf")
    print("│       └── 2025-08-31.pdf")
    print("└── icici/")
    print("    └── 2025/")
    print("        └── 2025-08-31.pdf")
    print()
    
    print("Usage:")
    print("-" * 30)
    print("1. Set the STATEMENTS_FOLDER environment variable:")
    print("   export STATEMENTS_FOLDER=/path/to/your/organized/statements")
    print()
    print("2. Run the rename command:")
    print("   python main.py --financial-institution ipay --feature rename-file --statements-folder statements/adp-ipay")
    print()
    print("3. Files will be automatically organized by institution and year")

if __name__ == "__main__":
    demonstrate_file_organization() 