import sys
import os
import re

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pdf_reader import extract_content

pdf_path = r"c:\Users\DELL\OneDrive\Desktop\AIML Project\quotation-ai\backend\uploads\Plumber Bathware.pdf"

print(f"Checking PDF: {pdf_path}")
# Brand is auto-detected from filename "Plumber Bathware.pdf"
items = extract_content(pdf_path)

print(f"Total items extracted: {len(items)}")

target = "DUN-1101"
found = False
for item in items:
    if target in item.get("text", ""):
        print(f"Found {target}:")
        print(f"Brand: {item.get('brand')}")
        print(f"Price: {item.get('price')}")
        print(f"Variant Prices: {item.get('variant_prices')}")
        print(f"Text snippet: {item.get('text')[:100]}")
        found = True

if not found:
    print(f"{target} not found in extraction results.")
