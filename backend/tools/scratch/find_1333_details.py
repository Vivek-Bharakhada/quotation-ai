import json

INDEX_PATH = "search_index_v2.json"

def main():
    with open(INDEX_PATH, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
        items = data.get("stored_items", [])

    codes_to_check = ["1333", "11333"]
    found_items = []
    for item in items:
        code = str(item.get("search_code", ""))
        if any(c in code for c in codes_to_check):
            found_items.append(item)

    print(json.dumps(found_items, indent=2))

if __name__ == "__main__":
    main()
