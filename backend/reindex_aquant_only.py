import sys
import os
import json

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import search_engine
from pdf_reader import extract_content

def reindex_aquant_only():
    print("--- STARTING AQUANT-ONLY RE-INDEX ---")
    
    # 1. Load existing index
    if os.path.exists(search_engine.INDEX_FILE):
        search_engine.load_index()
        print(f"Loaded existing index with {len(search_engine.stored_items)} items.")
    else:
        print("No existing index found, starting fresh.")
        search_engine.reset_index()

    # 2. Filter out old Aquant items
    old_count = len(search_engine.stored_items)
    search_engine.stored_items = [item for item in search_engine.stored_items if item.get('brand') != 'Aquant']
    removed = old_count - len(search_engine.stored_items)
    print(f"Removed {removed} old Aquant items.")

    # 3. Extract new Aquant items
    pdf_path = r"uploads\Aquant Price List Vol 15. Feb 2026_Searchable.pdf"
    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF not found at {pdf_path}")
        return

    print(f"Extracting from {pdf_path}...")
    new_items = extract_content(pdf_path)
    for item in new_items:
        item["brand"] = "Aquant"
        item["source"] = os.path.basename(pdf_path)

    # 4. Add to index
    search_engine.add_to_index(None, new_items)
    print(f"Added {len(new_items)} new Aquant items.")

    # 5. Save index
    search_engine.save_index()
    print("--- RE-INDEX COMPLETE ---")

if __name__ == "__main__":
    reindex_aquant_only()
