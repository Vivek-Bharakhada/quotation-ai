import sys
import os
import json

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pdf_reader import extract_content

pdf_path = r"uploads\Aquant Price List Vol 15. Feb 2026_Searchable.pdf"

print(f"--- EXTRACTING FROM {pdf_path} ---")
items = extract_content(pdf_path, max_pages=15) # First 15 pages

print(f"Extracted {len(items)} items.")

for idx, item in enumerate(items[:20]):
    print(f"\nITEM {idx+1}:")
    print(f"  Name: {item.get('name')}")
    print(f"  Price: {item.get('price')}")
    print(f"  Page: {item.get('page')}")
    # print(f"  Text: {item.get('text')[:100]}...")
