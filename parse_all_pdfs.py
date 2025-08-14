#!/usr/bin/env python3
"""Simple script to recursively parse all PDF files and print their text content."""

import sys
from pathlib import Path

import pdfplumber


def extract_pdf_text(pdf_file: Path) -> str:
    """Extract text content from a PDF file using pdfplumber."""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            text_content = []
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text_content.append(f"[Page {page_num}]\n{page_text}")
                else:
                    text_content.append(f"[Page {page_num}] - No text extracted")

            return "\n\n".join(text_content)
    except Exception as e:
        return f"ERROR: Could not extract text - {str(e)}"


def find_pdf_files(directory: Path) -> list[Path]:
    """Recursively find all PDF files in the given directory."""
    pdf_files = []
    for item in directory.rglob("*.pdf"):
        if item.is_file():
            pdf_files.append(item)
    return sorted(pdf_files)


def main():
    """Main function to parse all PDFs."""
    # Get directory from command line or use current directory
    if len(sys.argv) > 1:
        target_dir = Path(sys.argv[1])
    else:
        target_dir = Path.cwd()

    if not target_dir.exists():
        print(f"Error: Directory '{target_dir}' does not exist")
        return

    print(f"Searching for PDF files in: {target_dir}")
    print("=" * 60)

    # Find all PDF files
    pdf_files = find_pdf_files(target_dir)

    if not pdf_files:
        print("No PDF files found!")
        return

    print(f"Found {len(pdf_files)} PDF file(s):")
    for pdf_file in pdf_files:
        print(f"  - {pdf_file}")
    print()

    # Process each PDF file
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"Processing PDF {i}/{len(pdf_files)}: {pdf_file.name}")
        print("-" * 60)

        # Extract text content
        text_content = extract_pdf_text(pdf_file)

        # Print with filename suffix for every line
        print(f"[{pdf_file.name}] Content:")
        lines = text_content.split("\n")
        for line in lines:
            if line.strip():  # Only print non-empty lines
                print(f"{line} [{pdf_file.name}]")
        print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
