import json
import os

index_path = r"c:\Users\DELL\OneDrive\Desktop\AIML Project\quotation-ai\backend\search_index_v2.json"

if os.path.exists(index_path):
    with open(index_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    stored_items = data.get("stored_items", [])
    print(f"Total items in index: {len(stored_items)}")
    
    found = False
    for item in stored_items:
        text = item.get("text", "")
        if "DUN-1101" in text:
            print(f"Found product matching 'DUN-1101':")
            print(f"Name: {item.get('name')}")
            print(f"Brand: {item.get('brand')}")
            print(f"Variant Prices: {item.get('variant_prices')}")
            print(f"Text: {text[:200]}...")
            found = True
            break
    
    if not found:
        print("DUN-1101 not found in index.")
else:
    print("Index file not found.")
