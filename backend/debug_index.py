import json
import os

index_path = r"c:\Users\DELL\OneDrive\Desktop\AIML Project\quotation-ai\backend\search_index_v2.json"

if os.path.exists(index_path):
    with open(index_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    items = data if isinstance(data, list) else data.get("items", [])
        
    plumber_items = [i for i in items if i.get("brand") == "Plumber"]
    print(f"Total items: {len(items)}")
    print(f"Plumber items: {len(plumber_items)}")
    
    if plumber_items:
        for i in plumber_items[:5]:
            print(f"Text: {i.get('text').split('\n')[0]}")
            print(f"Variants: {i.get('variant_prices')}")
            print("-" * 10)
    else:
        print("No plumber items found in index.")
else:
    print("Index not found")
