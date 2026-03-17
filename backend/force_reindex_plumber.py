import os
import search_engine
from pdf_reader import extract_content

path = 'uploads/Plumber Bathware.pdf'
if os.path.exists(path):
    print(f"Re-indexing {path}...")
    items = extract_content(path)
    
    # Load current index
    search_engine.load_index()
    
    # Remove existing Plumber items
    old_count = len(search_engine.stored_items)
    search_engine.stored_items = [i for i in search_engine.stored_items if i.get('brand','').lower() != 'plumber']
    new_count = len(search_engine.stored_items)
    print(f"Removed {old_count - new_count} old Plumber items.")
    
    # Add new items
    search_engine.add_to_index(None, items)
    print(f"Added {len(items)} new Plumber items with variants.")
    
    # Save index
    search_engine.save_index()
    print("Done!")
else:
    print("PDF not found")
