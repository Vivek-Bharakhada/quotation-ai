import fitz
import re
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

pdf_path = "uploads/Aquant Price List Vol 15. Feb 2026_Searchable.pdf"
doc = fitz.open(pdf_path)

print("Searching for 1333 prices in Aquant PDF...")

for i, page in enumerate(doc):
    text = page.get_text()
    if "1333" in text:
        # Find lines with 1333 and look for amounts
        lines = text.splitlines()
        for j, line in enumerate(lines):
            if "1333" in line:
                print(f"Page {i} Line: {line}")
                # Look at next few lines for prices
                for k in range(j, min(j+5, len(lines))):
                    print(f"  Context: {lines[k]}")
