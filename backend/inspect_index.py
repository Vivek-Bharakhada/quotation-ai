import json
import os

index_path = "search_index_v2.json"
if os.path.exists(index_path):
    with open(index_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        items = data.get("stored_items", [])
        print(f"Total items: {len(items)}")
        for i, item in enumerate(items[:15]):
            name = item.get("name", "N/A")
            page = item.get("page", "?")
            images = i.get("images", []) if isinstance(i, dict) else item.get("images", [])
            print(f"[{i}] P{page} {name[:40]} -> {images}")
else:
    print("Index not found.")
