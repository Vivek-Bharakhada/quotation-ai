import json

path = r'c:\Users\DELL\OneDrive\Desktop\AIML Project\quotation-ai\backend\search_index_v2.json'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

items = data.get('stored_items') or data.get('items')
cats = sorted(set(i.get('category', 'None') for i in items if i.get('category')))
for c in cats:
    print(c)
