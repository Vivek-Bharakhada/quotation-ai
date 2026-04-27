import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "search_index_v2.json"
IMAGE_CACHE_PATH = ROOT / "image_path_cache.json"

sys.path.insert(0, str(ROOT))
import search_engine  # noqa: E402


def _load_index():
    return json.loads(INDEX_PATH.read_text(encoding="utf-8-sig"))


def _save_index(data):
    INDEX_PATH.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def _save_image_cache():
    image_root = ROOT / "static" / "images"
    cache = {}
    for current_root, _, files in os.walk(image_root):
        for filename in files:
            stem = Path(filename).stem
            compact = search_engine._compact_alnum(stem)
            if not compact:
                continue
            rel_dir = Path(current_root).relative_to(image_root).as_posix()
            rel_path = filename if rel_dir == "." else f"{rel_dir}/{filename}"
            cache.setdefault(compact, []).append(f"/static/images/{rel_path}")
    IMAGE_CACHE_PATH.write_text(
        json.dumps({"__schema__": search_engine.CACHE_SCHEMA_VERSION, "paths": cache}, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def main():
    data = _load_index()
    items = data.get("stored_items", [])

    search_engine._image_path_cache = None
    search_engine.item_code_meta_cache = {}

    changed = 0
    cleared = 0
    normalized = 0
    per_brand = {}

    for item in items:
        brand = str(item.get("brand") or "").strip().lower() or "unknown"
        stats = per_brand.setdefault(
            brand,
            {"total": 0, "resolved": 0, "missing": 0, "changed": 0, "cleared": 0},
        )
        stats["total"] += 1

        best_image = search_engine._best_item_image(item)
        current_images = [img for img in (item.get("images") or []) if img]
        current_first = current_images[0] if current_images else None

        if best_image:
            stats["resolved"] += 1
            normalized += 1
            new_images = [best_image]
            if current_images != new_images:
                item["images"] = new_images
                changed += 1
                stats["changed"] += 1
        else:
            stats["missing"] += 1
            if current_images:
                item["images"] = []
                changed += 1
                cleared += 1
                stats["changed"] += 1
                stats["cleared"] += 1

        if current_first != best_image and best_image:
            pass

    _save_index(data)
    _save_image_cache()

    print(f"Normalized items with resolved images: {normalized}")
    print(f"Index records changed: {changed}")
    print(f"Old/bad image paths cleared: {cleared}")
    print("")
    for brand in sorted(per_brand):
        stats = per_brand[brand]
        print(
            f"{brand}: total={stats['total']}, "
            f"resolved={stats['resolved']}, "
            f"missing={stats['missing']}, "
            f"changed={stats['changed']}, "
            f"cleared={stats['cleared']}"
        )


if __name__ == "__main__":
    main()
