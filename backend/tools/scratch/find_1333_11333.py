import fitz
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

pdf_path = "uploads/Aquant Price List Vol 15. Feb 2026_Searchable.pdf"
try:
    doc = fitz.open(pdf_path)
except Exception as e:
    print(f"Error opening Aquant PDF: {e}")
    # Try alternate path if not found
    pdf_path = "backend/uploads/Aquant Price List Vol 15. Feb 2026_Searchable.pdf"
    doc = fitz.open(pdf_path)

print(f"Searching for 1333 and 11333 prices in {pdf_path}...")

for i, page in enumerate(doc):
    text = page.get_text()
    if "1333" in text or "11333" in text:
        print(f"--- MATCH ON PAGE {i} ---")
        lines = text.splitlines()
        for j, line in enumerate(lines):
            if "1333" in line:
                print(f"L{j}: {line}")
                # Print context
                for k in range(max(0, j-2), min(len(lines), j+8)):
                    print(f"  {'>' if k==j else ' '} {lines[k]}")
