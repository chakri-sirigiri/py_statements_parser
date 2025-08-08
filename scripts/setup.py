#!/usr/bin/env python3
"""Setup script for Py Statements Parser."""

import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def main():
    """Main setup function."""
    print("Setting up Py Statements Parser...")
    
    # Check if uv is installed
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
        print("✓ uv is already installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Installing uv...")
        if not run_command(
            "curl -LsSf https://astral.sh/uv/install.sh | sh",
            "Install uv"
        ):
            print("Failed to install uv. Please install it manually from https://docs.astral.sh/uv/")
            return False
    
    # Install dependencies
    if not run_command("uv sync", "Install dependencies"):
        return False
    
    # Create necessary directories
    directories = [
        "data",
        "logs", 
        "statements/adp-ipay",
        "statements/icici",
        "statements/robinhood",
        "statements/first-energy",
        "statements/cash-app",
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")
    
    # Copy example config if it doesn't exist
    if not Path("config.yaml").exists():
        if Path("config.yaml.example").exists():
            import shutil
            shutil.copy("config.yaml.example", "config.yaml")
            print("✓ Created config.yaml from example")
        else:
            print("⚠ config.yaml.example not found")
    
    print("\nSetup completed successfully!")
    print("\nNext steps:")
    print("1. Place your PDF statement files in the appropriate statements/ folder")
    print("2. Run: python main.py --financial-institution ipay --feature rename-file --statements-folder statements/adp-ipay")
    print("3. Check the examples/ directory for more usage examples")


if __name__ == "__main__":
    main() 