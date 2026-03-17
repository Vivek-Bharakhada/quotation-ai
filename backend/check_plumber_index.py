import json
import os

index_path = r'c:\Users\DELL\OneDrive\Desktop\AIML Project\quotation-ai\backend\search_index_v2.json'
if os.path.exists(index_path):
    with open(index_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    items = data.get('stored_items', [])
    brands = set()
    for item in items:
        brands.add(item.get('brand'))
    print(f"Brands in index: {brands}")
    print(f"Total items: {len(items)}")
    
    # Check for Plumber specifically
    plumber_items = [i for i in items if i.get('brand') == 'Plumber']
    print(f"Plumber items: {len(plumber_items)}")
    if plumber_items:
        print("Sample Plumber item:", json.dumps(plumber_items[0], indent=2))
else:
    print("Index file not found")
