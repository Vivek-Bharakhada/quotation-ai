import json
import os

INDEX_FILE = 'backend/search_index_v2.json'
if os.path.exists(INDEX_FILE):
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    items = data.get('stored_items', [])
    plumber_items = [it for it in items if it.get('brand', '').lower() == 'plumber']
    print(f"Total Plumber items: {len(plumber_items)}")
    for it in plumber_items[:15]:
        print(f"Name: {it.get('name')} | Text: {it.get('text', '').replace('\\n', ' ')[:100]}")
else:
    print("Index not found")
