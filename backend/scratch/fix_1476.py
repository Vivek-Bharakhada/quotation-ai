import fitz
import os
import json

PDF_PATH = r"c:\Movies\quotation-ai\quotation-ai\backend\uploads\Aquant Price List Vol 15. Feb 2026_Searchable.pdf"
IMG_ROOT = r"c:\Movies\quotation-ai\quotation-ai\backend\static\images\Aquant"
INDEX_PATH = r"c:\Movies\quotation-ai\quotation-ai\backend\search_index_v2.json"

def fix_1476():
    doc = fitz.open(PDF_PATH)
    page = doc[36] # Page 37
    
    images = page.get_images(full=True)
    all_extracted = []
    for img in images:
        xref = img[0]
        rects = page.get_image_rects(xref)
        if not rects: continue
        r = rects[0]
        # Only row 1476
        if 360 < r.y0 < 450:
            base_image = doc.extract_image(xref)
            all_extracted.append({
                "rect": r,
                "bytes": base_image["image"]
            })
    
    # Sort by X then Y
    # Cluster 1 (Left): x ~ 57, y ~ 368 (Top), 404 (Bottom)
    # Cluster 2 (Middle): x ~ 243, y ~ 368, 404
    # Cluster 3 (Right): x ~ 421, y ~ 368, 404
    all_extracted.sort(key=lambda x: (x["rect"].x0, x["rect"].y0))
    
    print(f"Found {len(all_extracted)} images for 1476")
    
    mapping = {
        0: "BRG", # Top Left
        1: "BG",  # Bottom Left
        2: "GG",  # Top Middle
        3: "MB",  # Bottom Middle
        4: "RG",  # Top Right
        5: "CP"   # Bottom Right
    }
    
    with open(INDEX_PATH, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    
    fixed = 0
    for i, img_info in enumerate(all_extracted):
        suffix = mapping.get(i)
        if not suffix: continue
        
        filename = f"1476{suffix}.png"
        filepath = os.path.join(IMG_ROOT, filename)
        with open(filepath, "wb") as f:
            f.write(img_info["bytes"])
        
        full_code = f"1476 {suffix}"
        for item in data["stored_items"]:
            if item.get("search_code") == full_code or item.get("name").startswith(full_code):
                item["images"] = [f"/static/images/Aquant/{filename}"]
                fixed += 1
                print(f"Fixed {full_code} -> {filename}")
                break
    
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Total fixed: {fixed}")

if __name__ == "__main__":
    fix_1476()
