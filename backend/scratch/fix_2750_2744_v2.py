import fitz
import os
import json

PDF_PATH = r"c:\Movies\quotation-ai\quotation-ai\backend\uploads\Aquant Price List Vol 15. Feb 2026_Searchable.pdf"
IMG_ROOT = r"c:\Movies\quotation-ai\quotation-ai\backend\static\images\Aquant"
INDEX_PATH = r"c:\Movies\quotation-ai\quotation-ai\backend\search_index_v2.json"

def fix_2750_2744_correct_v2():
    doc = fitz.open(PDF_PATH)
    page = doc[47]
    
    images = page.get_images(full=True)
    all_extracted = []
    for img in images:
        xref = img[0]
        rects = page.get_image_rects(xref)
        if not rects: continue
        r = rects[0]
        base_image = doc.extract_image(xref)
        all_extracted.append({
            "rect": r,
            "bytes": base_image["image"],
            "ext": base_image["ext"]
        })
    
    # Corrected ranges based on analysis:
    # 2750 Double Tower Bar: y between 500 and 620
    row_2750 = [i for i in all_extracted if 500 < i["rect"].y0 < 620]
    # 2744 Napkin Holder: y between 650 and 780
    row_2744 = [i for i in all_extracted if 650 < i["rect"].y0 < 780]
    
    # Sort by X then Y
    row_2750.sort(key=lambda x: (x["rect"].x0, x["rect"].y0))
    row_2744.sort(key=lambda x: (x["rect"].x0, x["rect"].y0))
    
    print(f"Found {len(row_2750)} images for 2750 and {len(row_2744)} for 2744")
    
    mapping = {
        0: "BRG", # Top Left
        1: "BG",  # Bottom Left
        2: "GG",  # Top Middle
        3: "MB",  # Bottom Middle
        4: "CP"   # Right
    }
    
    with open(INDEX_PATH, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    
    def update_set(items_list, base_code):
        fixed = 0
        for i, img_info in enumerate(items_list):
            suffix = mapping.get(i)
            if not suffix: continue
            
            filename = f"{base_code}{suffix}.png"
            filepath = os.path.join(IMG_ROOT, filename)
            with open(filepath, "wb") as f:
                f.write(img_info["bytes"])
            
            full_code = f"{base_code} {suffix}"
            for item in data["stored_items"]:
                if item.get("search_code") == full_code or item.get("name").startswith(full_code):
                    item["images"] = [f"/static/images/Aquant/{filename}"]
                    fixed += 1
                    print(f"Fixed {full_code} -> {filename}")
                    break
        return fixed

    total_fixed = update_set(row_2750, "2750")
    total_fixed += update_set(row_2744, "2744")
    
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Total fixed: {total_fixed}")

if __name__ == "__main__":
    fix_2750_2744_correct_v2()
