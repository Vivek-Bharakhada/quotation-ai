"""
COMPLETE Kohler Image Sync Script
- Source of truth: backend/static/images/Kohler (user's 1459 images)
- Syncs to ALL app locations (installed app, win-unpacked, etc.)
- Rebuilds image cache from scratch
- Ensures every image has an index entry
"""
import os, sys, shutil, json, re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import search_engine

# ── Source (User's perfect images) ──────────────────────────────────────────
SOURCE_DIR = r"C:\Movies\quotation-ai\quotation-ai\backend\static\images\Kohler"

# ── All destination locations to sync ────────────────────────────────────────
DEST_DIRS = [
    r"C:\Movies\quotation-ai\quotation-ai\Quotation_AI_Software_Final\win-unpacked\resources\backend_sidecar\_internal\static\images\Kohler",
    r"C:\Movies\quotation-ai\quotation-ai\backend\dist\backend_sidecar\_internal\static\images\Kohler",
    r"C:\Movies\quotation-ai\quotation-ai\frontend\dist_client\win-unpacked\resources\backend_sidecar\_internal\static\images\Kohler",
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Shreeji Ceramica", "resources", "backend_sidecar", "_internal", "static", "images", "Kohler"),
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Shreeji Ceramica", "static", "images", "Kohler"),
]

print("=" * 60)
print("STEP 1: Syncing Kohler images to all app locations...")
print("=" * 60)

source_files = [f for f in os.listdir(SOURCE_DIR) if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]
print(f"Source images found: {len(source_files)}")

for dest in DEST_DIRS:
    if not os.path.exists(dest):
        try:
            os.makedirs(dest, exist_ok=True)
            print(f"  Created: {dest}")
        except Exception as e:
            print(f"  Skip (cant create): {dest} -> {e}")
            continue
    
    copied = 0
    for fname in source_files:
        src = os.path.join(SOURCE_DIR, fname)
        dst = os.path.join(dest, fname)
        # Always overwrite with source (source is truth)
        try:
            shutil.copy2(src, dst)
            copied += 1
        except Exception as e:
            print(f"    ERROR copying {fname}: {e}")
    
    # Remove any files in dest that are NOT in source (cleanup old images)
    dest_files = [f for f in os.listdir(dest) if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]
    removed = 0
    source_set = set(f.lower() for f in source_files)
    for fname in dest_files:
        if fname.lower() not in source_set:
            try:
                os.remove(os.path.join(dest, fname))
                removed += 1
            except:
                pass
    
    print(f"  {os.path.basename(os.path.dirname(dest))}: {copied} synced, {removed} removed")

print()
print("=" * 60)
print("STEP 2: Rebuilding image path cache from scratch...")
print("=" * 60)

# Delete old cache to force full rebuild
cache_file = r"C:\Movies\quotation-ai\quotation-ai\backend\image_path_cache.json"
if os.path.exists(cache_file):
    os.remove(cache_file)
    print("  Deleted old image_path_cache.json")

search_engine._image_path_cache = None  # force rebuild in memory
image_cache = search_engine._build_image_path_cache()
print(f"  New cache built: {len(image_cache)} unique code entries")

print()
print("=" * 60)
print("STEP 3: Loading index and ensuring every image has an entry...")
print("=" * 60)

search_engine.load_index()
print(f"  Current index: {len(search_engine.stored_items)} items")

def compact(s):
    return re.sub(r'[^a-z0-9]', '', str(s).lower())

# Build compact code -> item map from existing index (Kohler only)
existing_compacts = set()
for item in search_engine.stored_items:
    if item.get("brand") == "Kohler":
        meta = search_engine._get_item_code_metadata(item)
        for key in ("full_compact", "base_compact"):
            v = meta.get(key, "")
            if v:
                existing_compacts.add(v)
        # also check item name
        existing_compacts.add(compact(item.get("name", "").split(" - ")[0].split(" ")[0]))

new_items = []
no_match = []

for fname in source_files:
    stem = os.path.splitext(fname)[0]  # e.g. "K-705087IN-SHP"
    img_path = f"/static/images/Kohler/{fname}"
    
    # Try multiple compact variants for matching
    variants = [
        compact(stem),                           # k705087inshp
        compact(stem.lstrip("K-").lstrip("k-")), # 705087inshp
    ]
    # Remove 'k' prefix variant
    c = compact(stem)
    if c.startswith("k"):
        variants.append(c[1:])                   # 705087inshp

    found = any(v in existing_compacts for v in variants if v)
    
    if not found:
        no_match.append((stem, img_path))

print(f"  Images with NO index entry: {len(no_match)}")

for stem, img_path in no_match:
    new_items.append({
        "name": f"{stem} (Kohler)",
        "text": f"Kohler product {stem}",
        "price": "0",
        "page": 0,
        "source": "Manual Entry",
        "images": [img_path],
        "brand": "Kohler",
        "category": "Miscellaneous",
        "search_code": stem,
        "base_code": stem,
        "full_code": stem,
    })

if new_items:
    print(f"  Adding {len(new_items)} new entries...")
    search_engine.add_to_index(None, new_items)

# Now update ALL existing Kohler items to use the correct image from SOURCE
print()
print("  Verifying image paths for ALL Kohler items in index...")
updated = 0
source_compact_map = {}  # compact -> filename
for fname in source_files:
    stem = os.path.splitext(fname)[0]
    c = compact(stem)
    source_compact_map[c] = fname
    if c.startswith("k"):
        source_compact_map[c[1:]] = fname  # without K prefix

for item in search_engine.stored_items:
    if item.get("brand") != "Kohler":
        continue
    meta = search_engine._get_item_code_metadata(item)
    fc = meta.get("full_compact", "")
    bc = meta.get("base_compact", "")
    
    matched_file = source_compact_map.get(fc) or source_compact_map.get(bc)
    if matched_file:
        correct_path = f"/static/images/Kohler/{matched_file}"
        if item.get("images") != [correct_path]:
            item["images"] = [correct_path]
            updated += 1

print(f"  Updated {updated} Kohler items with correct image paths")

print()
print("=" * 60)
print("STEP 4: Saving final index...")
print("=" * 60)
search_engine.save_index()
print(f"  Saved! Total items: {len(search_engine.stored_items)}")

print()
print("=" * 60)
print("DONE! Summary:")
print(f"  Source images:   {len(source_files)}")
print(f"  Index items:     {len(search_engine.stored_items)}")
print(f"  New entries:     {len(new_items)}")
print(f"  Path updates:    {updated}")
print("=" * 60)
