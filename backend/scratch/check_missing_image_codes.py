import json
import os

INDEX = r'c:\Movies\quotation-ai\quotation-ai\backend\search_index_v2.json'
with open(INDEX, 'r', encoding='utf-8') as f:
    data = json.load(f)

items = data.get('stored_items', [])
codes = [
    'K-24740IN-7',
    'K-24740IN-K4',
    'K-17663IN-0',
    'K-82958',
    'K-1042534',
    'K-1060831',
    'K-1063956',
    'K-1286731',
]

print(f"Total items in index: {len(items)}")
print()

for code in codes:
    code_lower = code.lower()
    found = False
    for item in items:
        t = str(item.get('text', '') or '').lower()
        n = str(item.get('name', '') or '').lower()
        if code_lower in t or code_lower in n:
            found = True
            print(f"FOUND: {code}")
            print(f"  name   = {item.get('name', '')}")
            print(f"  images = {item.get('images', [])}")
            print()
            break
    if not found:
        print(f"NOT IN INDEX: {code}")
        print()
