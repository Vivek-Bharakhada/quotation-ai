import json
from collections import defaultdict

with open("search_index_v2.json", "r", encoding="utf-8") as f:
    items = json.load(f)["stored_items"]

aquant = [i for i in items if i.get("brand") == "Aquant"]

# Group by numeric prefix + image
# This is to check if same product family has DIFFERENT images for DIFFERENT variants
prefix_to_variants = defaultdict(list)
for i in aquant:
    code = i.get("search_code", "")
    import re
    m = re.match(r'^(\d{3,4})', code)
    if m:
        prefix = m.group(1)
        prefix_to_variants[prefix].append(i)

report = []
for prefix, itms in sorted(prefix_to_variants.items()):
    if len(itms) <= 1: continue
    
    # Check if they all have images or shared/diff images
    imgs = set()
    for it in itms:
        if it.get("images"):
            imgs.add(it["images"][0])
    
    if len(imgs) > 1:
        report.append(f"Prefix {prefix}: MULTIPLE IMAGES ({len(imgs)})")
        for it in itms:
            img = it["images"][0][-30:] if it.get("images") else "NO_IMG"
            report.append(f"  P{it.get('page')} | {it.get('search_code',''):15s} | {it.get('price',''):7s} | {img}")
    elif len(imgs) == 1:
        # All variants sharing the SAME image
        pass # report.append(f"Prefix {prefix}: SHARED IMAGE - {len(itms)} variants")
    else:
        report.append(f"Prefix {prefix}: NO IMAGES - {len(itms)} variants")

with open("color_image_report.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(report))

print(f"Report generated. Found {len(report)} multi-image families.")
