import json

INDEX_PATH = "search_index_v2.json"

def main():
    with open(INDEX_PATH, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
        items = data.get("stored_items", [])

    found_items = []
    for item in items:
        code = str(item.get("search_code", ""))
        if "1336" in code and "+" not in code:
            found_items.append(item)

    print(json.dumps(found_items, indent=2))

if __name__ == "__main__":
    main()
