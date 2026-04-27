"""
Image verification: Check every item's image actually exists on disk
"""
import json, sys, os
sys.stdout.reconfigure(encoding='utf-8')

INDEX_PATH  = r'C:\Movies\quotation-ai\quotation-ai\backend\search_index_v2.json'
STATIC_ROOT = r'C:\Movies\quotation-ai\quotation-ai\backend'

with open(INDEX_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)
stored = data['stored_items']

print(f"Total items: {len(stored)}")

no_image_entry = []
image_missing_disk = []
image_ok = 0

for i, item in enumerate(stored):
    imgs = item.get('images', [])
    code = item.get('search_code') or item.get('base_code') or 'N/A'
    brand = item.get('brand', '?')

    if not imgs or imgs == []:
        no_image_entry.append((i, brand, code))
        continue

    img_rel = imgs[0].lstrip('/')
    full_path = os.path.join(STATIC_ROOT, img_rel)
    if not os.path.exists(full_path):
        image_missing_disk.append((i, brand, code, imgs[0]))
    else:
        image_ok += 1

print(f"\n✅ Images OK (file exists): {image_ok}")
print(f"❌ No image entry:          {len(no_image_entry)}")
print(f"❌ Image missing on disk:   {len(image_missing_disk)}")

if no_image_entry:
    print(f"\n--- NO IMAGE ENTRY ({len(no_image_entry)}) ---")
    for i, brand, code in no_image_entry:
        print(f"  [{i:04d}] [{brand}] {code}")

if image_missing_disk:
    print(f"\n--- IMAGE FILE MISSING ON DISK ({len(image_missing_disk)}) ---")
    for i, brand, code, img in image_missing_disk:
        print(f"  [{i:04d}] [{brand}] {code} | {img}")
