import sys
import os
import json

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pdf_reader import extract_content
import search_engine

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")

def force_reindex_all():
    print("--- STARTING FORCE RE-INDEX ---")
    search_engine.reset_index()
    
    files = [f for f in os.listdir(UPLOAD_DIR) if f.lower().endswith(".pdf")]
    
    for filename in files:
        brand = ""
        if "aquant" in filename.lower(): brand = "Aquant"
        elif "kohler" in filename.lower(): brand = "Kohler"
        elif "plumber" in filename.lower(): brand = "Plumber"
        else: continue
        
        path = os.path.join(UPLOAD_DIR, filename)
        print(f"Indexing {brand} from {filename}...")
        try:
            items = extract_content(path)
            # Ensure brand is set for each item
            for item in items:
                item["brand"] = brand
            
            search_engine.add_to_index(None, items)
            print(f"Success: {len(items)} items added.")
        except Exception as e:
            print(f"Error indexing {filename}: {e}")
            
    search_engine.save_index()
    print("--- RE-INDEX COMPLETE ---")

if __name__ == "__main__":
    force_reindex_all()
