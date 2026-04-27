import json
import os

INDEX_PATH = "search_index_v2.json"
data = json.load(open(INDEX_PATH, "r", encoding="utf-8-sig"))
items = data.get("stored_items", [])

itp_u_items = []
for item in items:
    sc = str(item.get("search_code", "")).upper()
    if sc.startswith("ITP") or sc.startswith("U"):
        itp_u_items.append(item)

print(f"Total ITP/U items found: {len(itp_u_items)}")

for i, item in enumerate(itp_u_items[:20]):
    sc = item.get("search_code")
    imgs = item.get("images", [])
    brand = item.get("brand")
    exists = False
    if imgs:
        rel_path = imgs[0].replace("/static/images/", "", 1).lstrip("/")
        full_path = os.path.join("static", "images", rel_path)
        exists = os.path.exists(full_path)
    
    print(f"{i}. {sc} | Brand: {brand} | Images: {imgs} | Found on disk: {exists}")
