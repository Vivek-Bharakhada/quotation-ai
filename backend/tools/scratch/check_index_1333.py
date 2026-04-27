import json

index_path = "backend/search_index_v2.json"
with open(index_path, "r", encoding="utf-8") as f:
    data = json.load(f)

search_terms = ["1333", "11333"]
found = []

for item in data:
    code = str(item.get("code", ""))
    search_code = str(item.get("search_code", ""))
    if any(term in code or term in search_code for term in search_terms):
        found.append(item)

print(f"Found {len(found)} items matchings {search_terms}")
for item in found:
    print(f"Code: {item.get('code')}, Search Code: {item.get('search_code')}, Price: {item.get('price')}, Name: {item.get('name')[:50]}")
