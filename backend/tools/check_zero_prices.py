import json

INDEX_PATH = "search_index_v2.json"

def main():
    with open(INDEX_PATH, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
        items = data.get("stored_items", [])

    zero_price_items = []
    for item in items:
        price = str(item.get("price", "")).strip()
        if price == "0" or not price:
            zero_price_items.append(item)

    print(f"Total items with 0 price: {len(zero_price_items)}")
    for i, item in enumerate(zero_price_items):
        brand = item.get("brand")
        code = item.get("search_code")
        name = item.get("name")
        print(f"{i}. {brand} | {code} | {name}")

if __name__ == "__main__":
    main()
