import json
import os
import re
import shutil


BASE_DIR = os.path.dirname(__file__)
INDEX_PATH = os.path.join(BASE_DIR, "search_index_v2.json")
IMAGE_DIR = os.path.join(BASE_DIR, "static", "images", "Kohler")
REPORT_PATH = os.path.join(BASE_DIR, "kohler_k_code_image_fix_report.csv")


def _normalize_code(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "").strip())


def _extract_code(name: str) -> str:
    raw = str(name or "").strip()
    if not raw:
        return ""
    return _normalize_code(raw.split(" - ", 1)[0].strip())


def _resolve_image_path(image_path: str) -> str:
    raw = str(image_path or "").strip().replace("/", os.sep)
    if not raw:
        return ""
    if os.path.isabs(raw) and os.path.exists(raw):
        return raw
    rel = raw.lstrip(os.sep)
    candidates = [
        os.path.join(BASE_DIR, rel),
        os.path.join(BASE_DIR, "static", "images", os.path.basename(rel)),
        os.path.join(BASE_DIR, "static", "images", "Kohler", os.path.basename(rel)),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return ""


def main():
    if not os.path.exists(INDEX_PATH):
        raise FileNotFoundError(f"Missing index file: {INDEX_PATH}")

    os.makedirs(IMAGE_DIR, exist_ok=True)

    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("stored_items", []) if isinstance(data, dict) else data

    fixed = 0
    skipped = 0
    rows = []
    used_targets = {}

    for item in items:
        if str(item.get("brand", "")).strip().lower() != "kohler":
            continue

        name = str(item.get("name", "")).strip()
        if not name.upper().startswith("K-"):
            continue

        code = _extract_code(name)
        images = item.get("images") or []
        if not code or not images:
            skipped += 1
            rows.append([name, code, "", "", "skipped"])
            continue

        source_path = _resolve_image_path(images[0])
        if not source_path or not os.path.exists(source_path):
            skipped += 1
            rows.append([name, code, images[0], "", "source_missing"])
            continue

        ext = os.path.splitext(source_path)[1] or ".png"
        target_name = f"{code}{ext.lower()}"
        target_path = os.path.join(IMAGE_DIR, target_name)

        # Keep the first mapped file as the canonical alias.
        if os.path.abspath(source_path) != os.path.abspath(target_path):
            shutil.copy2(source_path, target_path)

        used_targets[target_name] = source_path
        item["images"] = [f"/static/images/Kohler/{target_name}"]
        fixed += 1
        rows.append([name, code, images[0], f"/static/images/Kohler/{target_name}", "fixed"])

    with open(REPORT_PATH, "w", encoding="utf-8", newline="") as f:
        f.write("product_name,code,source_image,new_image,status\n")
        for row in rows:
            f.write(",".join('"' + str(col).replace('"', '""') + '"' for col in row) + "\n")

    # Persist the updated image mapping back into the index.
    if isinstance(data, dict):
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f)

    print(f"Alias report written: {REPORT_PATH}")
    print(f"Fixed: {fixed}")
    print(f"Skipped: {skipped}")
    print(f"New aliases created: {len(used_targets)}")


if __name__ == "__main__":
    main()
