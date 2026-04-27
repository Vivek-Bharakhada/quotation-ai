import filecmp
import json
import os
import shutil
from pathlib import Path

import search_engine


ROOT = Path(__file__).resolve().parent
SOURCE_INDEX_PATH = ROOT / "search_index_v2.json"
SOURCE_IMAGES_DIR = ROOT / "static" / "images"
APPDATA_DIR = Path(os.getenv("LOCALAPPDATA", "")).expanduser() / "Shreeji Ceramica"

INDEX_PATHS = [
    SOURCE_INDEX_PATH,
    APPDATA_DIR / "search_index_v2.json",
    APPDATA_DIR / "resources" / "backend_sidecar" / "search_index_v2.json",
    APPDATA_DIR / "resources" / "backend_sidecar" / "_internal" / "search_index_v2.json",
]

FIXED_IMAGE_OVERRIDES = {
    "1742": {
        "image": "/static/images/1742.png",
        "page": 81,
        "source": "Aquant Price List Vol 15. Feb 2026_Searchable",
    },
    "1641": {
        "image": "/static/images/1641.png",
        "page": 90,
        "source": "Aquant Price List Vol 15. Feb 2026_Searchable",
    },
    "1570": {
        "image": "/static/images/1570.png",
        "page": 90,
        "source": "Aquant Price List Vol 15. Feb 2026_Searchable",
    },
    "4007": {
        "image": "/static/images/4007.png",
        "page": 52,
        "source": "Aquant Price List Vol 15. Feb 2026_Searchable",
    },
    "1333 bm": {
        "image": "/static/images/1333BM.png",
        "page": 15,
        "source": "Aquant Price List Vol 15. Feb 2026_Searchable",
    },
    "11333 lm": {
        "image": "/static/images/11333 LM.png",
        "page": 15,
        "source": "Aquant Price List Vol 15. Feb 2026_Searchable",
    },
}


def _build_image_cache():
    cache = {}
    if not SOURCE_IMAGES_DIR.exists():
        return cache

    for path in SOURCE_IMAGES_DIR.rglob("*"):
        if not path.is_file():
            continue
        stem = path.stem
        compact = search_engine._compact_alnum(stem)
        if not compact:
            continue
        rel = path.relative_to(SOURCE_IMAGES_DIR).as_posix()
        public_path = f"/static/images/{rel}"
        cache.setdefault(compact, []).append(public_path)

    return cache


def _candidate_code_keys(item):
    meta = search_engine._get_item_code_metadata(item)
    candidates = []
    for key in ("full_code", "search_code", "base_code"):
        value = str(item.get(key, "") or meta.get(key, "")).strip()
        if value:
            candidates.append(value)

    name = str(item.get("name") or "").strip()
    if name:
        candidates.append(name.split("\n", 1)[0].strip())

    text = str(item.get("text") or "").strip()
    if text:
        candidates.append(text.split("\n", 1)[0].strip())

    seen = set()
    for candidate in candidates:
        compact = search_engine._compact_alnum(candidate)
        if compact and compact not in seen:
            seen.add(compact)
            yield compact


def _repair_item_image(item, image_cache):
    search_code = str(item.get("search_code") or "").strip().lower()
    override = FIXED_IMAGE_OVERRIDES.get(search_code)
    if override:
        changed = False
        if (item.get("images") or [None])[0] != override["image"]:
            item["images"] = [override["image"]]
            changed = True
        for key in ("page", "source"):
            if item.get(key) != override[key]:
                item[key] = override[key]
                changed = True
        return changed, override["image"]
    return False, None


def _public_to_rel(public_path: str) -> str:
    return str(public_path or "").replace("/static/images/", "", 1).lstrip("/")


def _image_root_for_index(index_path: Path) -> Path:
    return index_path.parent / "static" / "images"


def _needs_copy(source_path: Path, target_path: Path) -> bool:
    if not target_path.exists():
        return True
    if source_path.stat().st_size != target_path.stat().st_size:
        return True
    return not filecmp.cmp(source_path, target_path, shallow=False)


def _sync_image(public_path: str, target_root: Path) -> bool:
    rel = _public_to_rel(public_path)
    if not rel:
        return False

    source_path = SOURCE_IMAGES_DIR / rel
    if not source_path.exists() or not source_path.is_file():
        return False

    target_path = target_root / rel
    if source_path.resolve() == target_path.resolve():
        return False

    target_path.parent.mkdir(parents=True, exist_ok=True)
    if _needs_copy(source_path, target_path):
        shutil.copy2(source_path, target_path)
        return True
    return False


def _backup_index(index_path: Path) -> Path:
    backup_path = index_path.with_suffix(".json.bak")
    if not backup_path.exists():
        backup_path.write_bytes(index_path.read_bytes())
    return backup_path


def repair_index(index_path: Path, image_cache):
    if not index_path.exists():
        return None

    backup_path = _backup_index(index_path)
    data = json.loads(index_path.read_text(encoding="utf-8-sig"))
    items = data.get("stored_items", [])
    image_root = _image_root_for_index(index_path)

    changed = 0
    matched = 0
    synced = 0

    for item in items:
        item_changed, resolved_path = _repair_item_image(item, image_cache)
        if item_changed:
            changed += 1
        if resolved_path:
            matched += 1
            if _sync_image(resolved_path, image_root):
                synced += 1

    index_path.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    return {
        "path": str(index_path),
        "backup": str(backup_path),
        "changed": changed,
        "matched": matched,
        "synced": synced,
    }


def main():
    image_cache = _build_image_cache()
    if not image_cache:
        raise SystemExit(f"Missing source images directory: {SOURCE_IMAGES_DIR}")

    results = []
    for index_path in INDEX_PATHS:
        result = repair_index(index_path, image_cache)
        if result:
            results.append(result)

    if not results:
        raise SystemExit("No search_index_v2.json files found to repair.")

    for result in results:
        print(
            f"{result['path']}: "
            f"{result['changed']} index updates, "
            f"{result['matched']} matched items, "
            f"{result['synced']} image syncs"
        )
        print(f"Backup saved at: {result['backup']}")


if __name__ == "__main__":
    main()
