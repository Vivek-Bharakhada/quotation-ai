"""Fix remaining Aquant items that the first pass couldn't resolve."""
import json
import os
import re

INDEX_PATH = "search_index_v2.json"
IMG_DIR = os.path.join("static", "images")


def compact(s):
    return re.sub(r"[^a-z0-9]+", "", s.lower())


# Manual mappings for known tricky items
MANUAL_FIXES = {
    # 2096 variants - on disk as 2096B, 2096BR, 2096CP, 2096G, 2096M, 2096R
    "2096 BRG": "/static/images/2096BR.png",
    "2096 BG": "/static/images/2096B.png",
    "2096 GG": "/static/images/2096G.png",
    "2096 MB": "/static/images/2096M.png",
    "2096 RG": "/static/images/2096R.png",
    "2096 CP": "/static/images/2096CP.png",
    # 2098 variants - on disk as 2098B, 2098BR, 2098CP, 2098G, 2098M, 2098R
    "2098 BRG": "/static/images/2098BR.png",
    "2098 BG": "/static/images/2098B.png",
    "2098 GG": "/static/images/2098G.png",
    "2098 MB": "/static/images/2098M.png",
    "2098 RG": "/static/images/2098R.png",
    "2098 CP": "/static/images/2098CP.png",
    # 750080 -> 75080
    "750080 BS": "/static/images/75080BS.png",
    "750080 BS CH": "/static/images/75080BSCH.png",
    "750080 TL": "/static/images/75080TL.png",
    "750080 TI": "/static/images/75080TI.png",
    # Others
    "1432": "/static/images/1432TILE.png",
    "3131": "/static/images/3131SS.png",
    "30006": "/static/images/30006CP.png",
    # 7008 ORY variants -> use base 7008 images
    "7008 RG ORY": "/static/images/7008RG.png",
    "7008 GG ORY": "/static/images/7008GG.png",
    "7008 BG ORY": "/static/images/7008BG.png",
    # 7009 + 9245 CM OASIS GRACE -> use base 7009 images
    "7009 RG + 9245 CM OASIS GRACE": "/static/images/7009RG+9245CM.png",
    "7009 BG + 9245 CM OASIS GRACE": "/static/images/7009BG+9245CM.png",
    "7009 GG + 9245 CM OASIS GRACE": "/static/images/7009GG+9245CM.png",
    # 7512 TCR + 7514 MB + 7513 combo
    "7512 TCR + 7514 MB + 7513": "/static/images/7512TCR+7514MB+7513TCR.png",
    # 2086/2512/2572 TALL variants
    "2086": "/static/images/2086TALL.png",
    "2512": "/static/images/2512TALL.png",
    "2572": "/static/images/2572TALL.png",
    "2023": "/static/images/2023TALL.png",
    "1485": "/static/images/1485ABS.png",
}


def main():
    data = json.load(open(INDEX_PATH, "r", encoding="utf-8-sig"))
    items = data.get("stored_items", [])

    fixed = 0
    still_broken = []

    for item in items:
        brand = (item.get("brand") or "").lower()
        source = (item.get("source") or "").lower()
        if "aquant" not in brand and "aquant" not in source:
            continue

        sc = (item.get("search_code") or "").strip()
        imgs = item.get("images") or []
        if not imgs:
            continue

        img_path = imgs[0]
        rel_path = img_path.replace("/static/images/", "", 1).lstrip("/")
        full_path = os.path.join(IMG_DIR, rel_path)
        file_exists = os.path.exists(full_path)

        img_filename = os.path.splitext(os.path.basename(img_path))[0]
        expected_compact = compact(sc)
        actual_compact = compact(img_filename)
        matches_code = expected_compact == actual_compact

        if file_exists and matches_code:
            continue

        # Check manual fixes
        if sc in MANUAL_FIXES:
            new_path = MANUAL_FIXES[sc]
            new_rel = new_path.replace("/static/images/", "", 1).lstrip("/")
            new_full = os.path.join(IMG_DIR, new_rel)
            if os.path.exists(new_full):
                item["images"] = [new_path]
                print(f"  FIXED: {sc}: {img_path} -> {new_path}")
                fixed += 1
                continue
            else:
                print(f"  MANUAL FIX FILE MISSING: {sc} -> {new_path}")

        # Accept close-enough matches (combo products like 1871 AB+ W -> 1871AB.png)
        if file_exists and not matches_code:
            # If the image base code is contained in the search code, accept it
            base_num = re.match(r"(\d+)", sc)
            img_base = re.match(r"(\d+)", img_filename)
            if base_num and img_base and base_num.group(1) == img_base.group(1):
                continue  # Close enough match, skip

        if not file_exists:
            still_broken.append(f"  STILL BROKEN: {sc} -> {img_path} (file missing)")
        else:
            still_broken.append(f"  STILL BROKEN: {sc} -> {img_path} (mismatch)")

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    print(f"\n=== RESULTS ===")
    print(f"Fixed: {fixed}")
    print(f"Still broken ({len(still_broken)}):")
    for s in still_broken:
        print(s)
    print(f"\nIndex saved to {INDEX_PATH}")


if __name__ == "__main__":
    main()
