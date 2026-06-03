import os
import sys
import json
from dotenv import load_dotenv

# Add backend directory to sys.path so we can import search_engine and mongodb
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environmental variables from .env
load_dotenv()

import search_engine
import mongodb

def main():
    index_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'search_index_v2.json'))
    if not os.path.exists(index_path):
        print(f"Index file not found at: {index_path}")
        return

    print(f"Loading existing index from {index_path}...")
    with open(index_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    stored_items = data.get('stored_items', [])
    print(f"Current items count: {len(stored_items)}")

    # Filter out any messy or duplicate items containing '24199'
    cleaned_items = []
    removed_items = []
    for item in stored_items:
        name = str(item.get('name', '')).upper()
        search_code = str(item.get('search_code', '')).upper()
        base_code = str(item.get('base_code', '')).upper()
        text = str(item.get('text', '')).upper()
        
        if '24199' in name or '24199' in search_code or '24199' in base_code or '24199' in text:
            removed_items.append(item)
        else:
            cleaned_items.append(item)

    print(f"Removed {len(removed_items)} matching items containing '24199':")
    for item in removed_items:
        print(f" - {item.get('name')} (Price: {item.get('price')})")

    # Define clean products
    item_c03 = {
        "text": "Patio™ Urinal sensor with AC adaptor (AC+DC) with flushing adjustable in polished chrome\nK-24199IN-C03-CP\nKohler",
        "name": "K-24199IN-C03-CP - Patio™ Urinal sensor with AC adaptor (AC+DC) with flushing adjustable in polished chrome",
        "price": "26400.00",
        "page": 164,
        "source": "Kohler_Pricebook (March'26)",
        "images": [
            "/static/images/Kohler/K-24199IN-C03-CP.png"
        ],
        "brand": "Kohler",
        "category": "Commercial Products",
        "base_code": "K-24199IN-C03",
        "variant_code": "CP",
        "search_code": "K-24199IN-C03-CP",
        "finish_label": "Chrome Plated",
        "base_compact": "k24199inc03",
        "variant_compact": "cp",
        "full_compact": "k24199inc03cp"
    }

    item_c01 = {
        "text": "Patio™ Urinal sensor in polished chrome\nK-24199IN-C01-CP\nKohler",
        "name": "K-24199IN-C01-CP - Patio™ Urinal sensor in polished chrome",
        "price": "27000.00",
        "page": 164,
        "source": "Kohler_Pricebook (March'26)",
        "images": [
            "/static/images/Kohler/K-24199IN-C01-CP.png"
        ],
        "brand": "Kohler",
        "category": "Commercial Products",
        "base_code": "K-24199IN-C01",
        "variant_code": "CP",
        "search_code": "K-24199IN-C01-CP",
        "finish_label": "Chrome Plated",
        "base_compact": "k24199inc01",
        "variant_compact": "cp",
        "full_compact": "k24199inc01cp"
    }

    cleaned_items.append(item_c03)
    cleaned_items.append(item_c01)
    print(f"Added K-24199IN-C03-CP and K-24199IN-C01-CP. Total cleaned items count: {len(cleaned_items)}")

    # Reset search engine state
    search_engine.reset_index()
    
    # Re-index all items
    search_engine.add_to_index(None, cleaned_items)

    # Save to local file
    search_engine.save_index()
    print("Successfully saved local index.")

    # Save to MongoDB if enabled
    if mongodb.is_enabled():
        print("MongoDB is enabled. Syncing new search index to cloud...")
        data = {
            "stored_items": search_engine.stored_items,
            "keyword_index": search_engine.keyword_index
        }
        mongodb.save_search_index(data)
        print("MongoDB Cloud Sync Complete.")
    else:
        print("Warning: MongoDB is not enabled or URI is missing. Cannot sync to cloud.")

if __name__ == "__main__":
    main()
