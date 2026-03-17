import json
import os

index_path = r"c:\Users\DELL\OneDrive\Desktop\AIML Project\quotation-ai\backend\search_index_v2.json"

if os.path.exists(index_path):
    with open(index_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    plumber_items = [i for i in data if i.get("brand") == "Plumber"]
    print(f"Total Plumber items: {len(plumber_items)}")
    
    for item in plumber_items:
        if "DUN-1101" in item.get("name", ""):
            print(f"Found DUN-1101:")
            print(f"Brand: {item.get('brand')}")
            print(f"Variant Prices: {item.get('variant_prices')}")
            break
else:
    print("Index not found")
