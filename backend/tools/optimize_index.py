import sys
import os

# Add current dir to path to import search_engine
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import search_engine

def run_optimization():
    print("Starting Deep Search Index Optimization...")
    
    # 1. Load the index (this will trigger enrichment and image cache building)
    success = search_engine.load_index(force=True)
    if not success:
        print("Failed to load index. Please ensure search_index_v2.json exists.")
        return

    print(f"Index loaded. {len(search_engine.stored_items)} items found.")
    
    # 2. Re-force enrichment and quality bonus calculation
    print("Processing items...")
    for item in search_engine.stored_items:
        # Pre-calculate metadata and store it directly in the item
        meta = search_engine._get_item_code_metadata(item)
        item["base_code"] = meta["base_code"]
        item["variant_code"] = meta["variant_code"]
        item["search_code"] = meta["full_code"]
        item["base_compact"] = meta["base_compact"]
        item["variant_compact"] = meta["variant_compact"]
        item["full_compact"] = meta["full_compact"]
        if meta["finish_label"] and not item.get("finish_label"):
            item["finish_label"] = meta["finish_label"]
            
        # Ensure image is normalized
        best_img = search_engine._best_item_image(item)
        if best_img:
            item["images"] = [best_img]

    # 3. Clean up keyword index (it will be rebuilt during load anyway, but we save it now)
    # Rebuild keyword index correctly
    print("Rebuilding keyword index...")
    new_keyword_index = {}
    for i, item in enumerate(search_engine.stored_items):
        words = set()
        name = str(item.get("name", "")).lower()
        text = str(item.get("text", "")).lower()
        
        # Add basic words
        import re
        for w in re.split(r'[\s\-\/\.\_\u2013\u2014]+', name + " " + text):
            if len(w) >= 2:
                words.add(w)
        
        # Add compact codes
        for key in ("full_compact", "base_compact", "variant_compact"):
            val = item.get(key)
            if val and len(val) >= 2:
                words.add(val)
                
        for w in words:
            new_keyword_index.setdefault(w, []).append(i)

    search_engine.keyword_index = new_keyword_index
    
    # 4. Save optimized index
    print("Saving optimized index and image cache...")
    search_engine.save_index()
    print("Optimization Complete!")

if __name__ == "__main__":
    run_optimization()
