import json

index_path = "backend/search_index_v2.json"
with open(index_path, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Data type: {type(data)}")
if isinstance(data, list):
    print(f"List length: {len(data)}")
    if len(data) > 0:
        print(f"First item type: {type(data[0])}")
        print(f"First item: {data[0]}")
elif isinstance(data, dict):
    print(f"Dict keys: {list(data.keys())[:10]}")
    first_key = list(data.keys())[0]
    print(f"First value type: {type(data[first_key])}")
    print(f"First value: {data[first_key]}")
