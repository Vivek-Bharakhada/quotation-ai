import json

INDEX_PATH = "search_index_v2.json"

def main():
    with open(INDEX_PATH, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
        items = data.get("stored_items", [])

    found_items = []
    for item in items:
        if item.get("price") == "69500" and item.get("brand") == "Aquant":
            found_items.append(item)

    print(json.dumps(found_items, indent=2))

if __name__ == "__main__":
    main()
