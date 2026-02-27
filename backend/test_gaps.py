import json
import collections

with open('backend/search_index_v2.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

items = data.get('stored_items') or data.get('items') or []

zero_price = []
short_desc = []
missing_details = []

for item in items:
    price = item.get('price', '')
    if not price or price == '0':
        zero_price.append(item)
    
    text = item.get('text', '')
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    # Text contains name, and sometimes MRP. How many OTHER lines are there?
    desc_lines = [l for l in lines if l != item['name'] and 'MRP' not in l.upper()]
    if len(desc_lines) == 0:
        missing_details.append(item)

print(f"Total Items: {len(items)}")
print(f"Items with 0 or empty price: {len(zero_price)}")
print(f"Items with NO remaining description: {len(missing_details)}")

print("\n--- SAMPLE ZERO PRICE ---")
for i in zero_price[:5]:
    print(i['name'], "-->", repr(i['text']))

print("\n--- SAMPLE MISSING DETAILS ---")
for i in missing_details[:5]:
    print(i['name'], "-->", repr(i['text']))
