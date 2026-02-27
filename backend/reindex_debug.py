import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

import pdf_reader
import search_engine

pdf_path = r'c:\Users\DELL\OneDrive\Desktop\AIML Project\quotation-ai\backend\uploads\Aquant Price List Vol. 14 Feb. 2025 - Low Res Searchable.pdf'

print("--- STARTING RE-INDEXING DEBUG ---")
items = pdf_reader.extract_content(pdf_path, max_pages=15)
print(f"Total items extracted: {len(items)}")

# Count items per category
stats = {}
for item in items:
    cat = item.get("category", "NONE")
    stats[cat] = stats.get(cat, 0) + 1

print("\nCategory Stats:")
for cat, count in stats.items():
    print(f"  {cat}: {count}")

# Save the index to update search_engine.stored_items
search_engine.add_to_index(None, items)
search_engine.save_index()
print("\n--- INDEX SAVED ---")
