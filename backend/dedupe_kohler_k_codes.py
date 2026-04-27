import json
import os
from collections import OrderedDict


BASE_DIR = os.path.dirname(__file__)
INDEX_PATH = os.path.join(BASE_DIR, "search_index_v2.json")
BACKUP_PATH = os.path.join(BASE_DIR, "search_index_v2.before_kohler_dedupe.json")


def _code_key(item):
    name = str(item.get("name", "")).strip()
    if not name.upper().startswith("K-"):
        return ""
    return name.split(" - ", 1)[0].strip().upper()


def _merge_items(primary, duplicate):
    # Keep the first item as canonical and merge useful data from duplicates.
    primary_images = list(primary.get("images") or [])
    duplicate_images = list(duplicate.get("images") or [])
    merged_images = OrderedDict()
    for img in primary_images + duplicate_images:
        if img and img not in merged_images:
            merged_images[img] = None
    primary["images"] = list(merged_images.keys())

    # Fill in any missing fields from the duplicate.
    for key, value in duplicate.items():
        if key == "images":
            continue
        if key not in primary or primary.get(key) in ("", None, [], {}):
            primary[key] = value

    return primary


def main():
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("Unexpected index structure; expected a dict with stored_items.")

    items = data.get("stored_items", [])
    if not isinstance(items, list):
        raise ValueError("Unexpected stored_items structure.")

    grouped = OrderedDict()
    passthrough = []

    for item in items:
        if str(item.get("brand", "")).strip().lower() != "kohler":
            passthrough.append(item)
            continue

        code = _code_key(item)
        if not code:
            passthrough.append(item)
            continue

        if code not in grouped:
            grouped[code] = item
        else:
            grouped[code] = _merge_items(grouped[code], item)

    deduped_kohler = list(grouped.values())
    data["stored_items"] = passthrough + deduped_kohler

    with open(BACKUP_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f)

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f)

    print(f"Backup written: {BACKUP_PATH}")
    print(f"Original Kohler K items: {sum(1 for it in items if str(it.get('brand','')).lower() == 'kohler' and str(it.get('name','')).strip().upper().startswith('K-'))}")
    print(f"Deduped Kohler K items: {len(deduped_kohler)}")
    print(f"Total stored_items after dedupe: {len(data['stored_items'])}")


if __name__ == "__main__":
    main()
