#!/usr/bin/env python3
"""Script to parse PDFs and highlight extraction patterns used by the project."""

import re
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


def highlight_extraction_patterns(text_content: str) -> str:
    """Highlight the specific patterns that the extraction logic looks for."""
    highlighted_lines = []

    # Define the key patterns from your project
    patterns = {
        "pay_date": r"Pay\s+Date[:\s]*(\d{1,2}/\d{1,2}/\d{4})",
        "regular_pay": r"Regular[:\s]*([\d,]+\.?\d*)",
        "bonus": r"Bonus[:\s]*([\d,]+\.?\d*)",
        "gross_pay": r"Gross\s+Pay[:\s]*([\d,]+\.?\d*)",
        "net_pay": r"Net\s+Pay[:\s]*([\d,]+\.?\d*)",
        "checking_accounts": r"checking\d*\s+(\d+\s+\d+\s+\d+)(?:\s+(\d+\s+\d+\s+\d+))?",
        "federal_tax": r"Federal\s+Income\s+Tax[:\s]*([-\d,]+\.?\d*)",
        "social_security": r"Social\s+Security\s+Tax[:\s]*([-\d,]+\.?\d*)",
        "medicare_tax": r"Medicare\s+Tax[:\s]*([-\d,]+\.?\d*)",
        "state_tax": r"OH\s+State\s+Income\s+Tax[:\s]*([-\d,]+\.?\d*)",
        "local_tax": r"Brooklyn\s+Income\s+Tax[:\s]*([-\d,]+\.?\d*)",
        "hsa_plan": r"HSA\s+Plan[:\s]*([-\d,]+\.?\d*)",
        "pretax_medical": r"Pretax\s+Medical[:\s]*([-\d,]+\.?\d*)",
        "pretax_dental": r"Pretax\s+Dental[:\s]*([-\d,]+\.?\d*)",
        "k401_pretax": r"401K\s+Pretax[:\s]*([-\d,]+\.?\d*)",
    }

    lines = text_content.split("\n")

    for line in lines:
        line_lower = line.lower()
        highlighted_line = line

        # Check each pattern
        for pattern_name, pattern_regex in patterns.items():
            matches = re.findall(pattern_regex, line, re.IGNORECASE)
            if matches:
                # Highlight the matched pattern
                highlighted_line = f"🔍 [{pattern_name.upper()}] {line}"
                break

        # Special highlighting for checking accounts
        if "checking" in line_lower:
            checking_matches = re.findall(r"checking\d*\s+(\d+\s+\d+\s+\d+)(?:\s+(\d+\s+\d+\s+\d+))?", line_lower)
            if checking_matches:
                highlighted_line = f"💰 [CHECKING_ACCOUNT] {line}"

        # Highlight lines with dollar amounts
        if re.search(r"\d+\s+\d+\s+\d+", line):
            highlighted_line = f"💵 [DOLLAR_AMOUNT] {line}"

        highlighted_lines.append(highlighted_line)

    return "\n".join(highlighted_lines)


def find_pdf_files(directory: Path) -> list[Path]:
    """Recursively find all PDF files in the given directory."""
    pdf_files = []
    for item in directory.rglob("*.pdf"):
        if item.is_file():
            pdf_files.append(item)
    return sorted(pdf_files)


def main():
    """Main function to parse all PDFs and highlight patterns."""
    # Get directory from command line or use current directory
    if len(sys.argv) > 1:
        target_dir = Path(sys.argv[1])
    else:
        target_dir = Path.cwd()

    if not target_dir.exists():
        print(f"Error: Directory '{target_dir}' does not exist")
        return

    print(f"Searching for PDF files in: {target_dir}")
    print("=" * 80)

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
        print("-" * 80)

        # Extract text content
        text_content = extract_pdf_text(pdf_file)

        # Highlight extraction patterns
        highlighted_content = highlight_extraction_patterns(text_content)

        # Print with filename prefix and pattern highlighting
        print(f"[{pdf_file.name}] Content with Pattern Highlighting:")
        print(highlighted_content)
        print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
