import os
import json
import re
import search_engine

print("Checking Kohler images for missing index items (Improved Matching)...")
search_engine.load_index()

images_dir = r"c:\Movies\quotation-ai\quotation-ai\backend\static\images\Kohler"
if not os.path.exists(images_dir):
    print("Kohler images directory not found")
    exit()

image_files = [f for f in os.listdir(images_dir) if f.lower().endswith(".png")]
print(f"Found {len(image_files)} Kohler images.")

# Map codes to items
code_to_item = {}
for item in search_engine.stored_items:
    if item.get("brand") == "Kohler":
        code_meta = search_engine._get_item_code_metadata(item)
        for key in ("full_code", "base_code", "full_compact", "base_compact"):
            val = str(code_meta.get(key) or "").lower()
            if val:
                # Store both with and without 'k' prefix for matching
                code_to_item.setdefault(val, []).append(item)
                if val.startswith("k"):
                    code_to_item.setdefault(val[1:], []).append(item)
                if val.startswith("k-"):
                    code_to_item.setdefault(val[2:], []).append(item)

missing_count = 0
added_items = []

for img_file in image_files:
    code_from_filename = os.path.splitext(img_file)[0]
    code_norm = re.sub(r'[\s\-]+', '', code_from_filename).lower()
    if code_norm.startswith("k"): code_norm = code_norm[1:]
    
    found = False
    if code_norm in code_to_item:
        found = True
    else:
        # Try finding if any item name contains this code
        for item in search_engine.stored_items:
            if item.get("brand") == "Kohler":
                name_clean = re.sub(r'[^a-z0-9]+', '', item.get("name", "").lower())
                if code_norm in name_clean:
                    found = True
                    break
    
    if not found:
        print(f"Missing item for image: {img_file}")
        missing_count += 1
        # Create a dummy item for the missing image
        dummy = {
            "name": f"{code_from_filename} (Kohler)",
            "text": f"Kohler product: {code_from_filename}\nSource: Manually added image",
            "price": "0",
            "page": 0,
            "source": "Manual Entry",
            "images": [f"/static/images/Kohler/{img_file}"],
            "brand": "Kohler",
            "category": "Miscellaneous",
            "search_code": code_from_filename
        }
        added_items.append(dummy)

if added_items:
    print(f"Adding {len(added_items)} dummy items for orphaned images...")
    search_engine.add_to_index(None, added_items)
    search_engine.save_index()
    print("Updated index with dummy items.")
else:
    print("All Kohler images have matching items in the index.")

print(f"Total missing: {missing_count}")
