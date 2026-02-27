import json

path = r'c:\Users\DELL\OneDrive\Desktop\AIML Project\quotation-ai\backend\search_index_v2.json'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

items = data.get('stored_items') or data.get('items') or []
print(f"Total: {len(items)}")

c_toilets = [i for i in items if i.get('category') == 'TOILETS']
print(f"Toilets: {len(c_toilets)}")
for i in c_toilets[:15]:
    print(f"{i.get('name')} | MRP: {i.get('price')} | Image: {i.get('images')}")
