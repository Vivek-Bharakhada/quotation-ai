import json
import os

INDEX_FILE = 'backend/search_index_v2.json'
with open(INDEX_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

items = data.get('stored_items', [])
print(f"Total items in index: {len(items)}")

targets = ["2734 AB", "2639 AB", "1961 + 1963 AB"]

for target in targets:
    found = [i for i in items if target in i.get('name', '') and i.get('brand') == 'Aquant']
    if found:
        # Sort by match quality (simple)
        found.sort(key=lambda x: len(x['name']))
        best = found[0]
        print(f"FOUND: {best['name']}")
        print(f"  Price: {best['price']}")
        print(f"  Images: {best.get('images', [])}")
        print(f"  Page: {best['page']}")
    else:
        print(f"NOT FOUND: {target}")
