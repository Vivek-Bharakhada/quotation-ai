import json
with open('search_index_v2.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    stored = data['stored_items']
    # Look for items containing '9272'
    matches = [i for i in stored if '9272' in i['text']]
    for m in matches[:3]:
        print(f"Source: {m.get('source')} | Text: {m['text'][:100]}")
