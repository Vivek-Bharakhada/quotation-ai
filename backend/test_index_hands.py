import json
path = r'backend/search_index_v2.json'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

for item in data.get('items', []):
    if item.get('category') == 'HAND SHOWERS IN SPECIAL FINISHES':
        lines = item.get('text', '').split('\n')
        desc = [l.strip() for l in lines if len(l.strip()) > 5 and l.strip() != item.get('name') and 'MRP' not in l.upper()]
        desc_str = ' • '.join(desc[:3]) if desc else "Premium Sanitaryware"
        print(f"[{item.get('name')}] Price: {item.get('price')} | Desc: {desc_str}")
