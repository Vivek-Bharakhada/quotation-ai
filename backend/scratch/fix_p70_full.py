import fitz
import os
import json

PDF_PATH = r"c:\Movies\quotation-ai\quotation-ai\backend\uploads\Aquant Price List Vol 15. Feb 2026_Searchable.pdf"
IMG_ROOT = r"c:\Movies\quotation-ai\quotation-ai\backend\static\images\Aquant"
INDEX_PATH = r"c:\Movies\quotation-ai\quotation-ai\backend\search_index_v2.json"

def fix_page_70_all():
    doc = fitz.open(PDF_PATH)
    page = doc[70] # Page 71
    
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
            "bytes": base_image["image"]
        })
    
    # Sort by Y then X
    # Rows:
    # 7515: Y ~ 45
    # Sets: Y ~ 328
    # 7513: Y ~ 650
    # 7514: Y ~ 650 (Far Right)
    
    row_7515 = sorted([i for i in all_extracted if 40 < i["rect"].y0 < 60], key=lambda x: x["rect"].x0)
    row_sets = sorted([i for i in all_extracted if 320 < i["rect"].y0 < 340], key=lambda x: x["rect"].x0)
    row_7513 = sorted([i for i in all_extracted if 640 < i["rect"].y0 < 660 and i["rect"].x0 < 400], key=lambda x: x["rect"].x0)
    item_7514 = sorted([i for i in all_extracted if 640 < i["rect"].y0 < 660 and i["rect"].x0 > 400], key=lambda x: x["rect"].x0)

    print(f"7515: {len(row_7515)}, Sets: {len(row_sets)}, 7513: {len(row_7513)}, 7514: {len(item_7514)}")
    
    colors = ["MI", "MG", "TCR", "OG"]
    
    with open(INDEX_PATH, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    
    def update(img_list, base_code_template, color_list):
        fixed = 0
        for i, img_info in enumerate(img_list):
            if i >= len(color_list): break
            color = color_list[i]
            
            code = base_code_template.replace("{COLOR}", color)
            filename = code.replace(" ", "") + ".png"
            filepath = os.path.join(IMG_ROOT, filename)
            
            with open(filepath, "wb") as f:
                f.write(img_info["bytes"])
            
            # Update index
            found = False
            for item in data["stored_items"]:
                # Match code or name
                if item.get("search_code") == code:
                    item["images"] = [f"/static/images/Aquant/{filename}"]
                    fixed += 1
                    found = True
                    print(f"Fixed {code} -> {filename}")
                    break
            
            if not found:
                # Try fuzzy matching for the set code which might be inconsistent
                if "+" in code:
                    # e.g. "7512 TCR + 7514 MB + 7513" vs "7512 TCR + 7514 MB + 7513 TCR"
                    prefix = code.split("+")[0].strip()
                    for item in data["stored_items"]:
                        if prefix in item.get("search_code", "") and "+" in item.get("search_code", ""):
                            item["images"] = [f"/static/images/Aquant/{filename}"]
                            fixed += 1
                            print(f"Fixed Fuzzy {item['search_code']} -> {filename}")
                            break
        return fixed

    total = 0
    total += update(row_7515, "7515 {COLOR}", colors)
    total += update(row_sets, "7512 {COLOR} + 7514 MB + 7513 {COLOR}", colors)
    total += update(row_7513, "7513 {COLOR}", colors)
    total += update(item_7514, "7514 MB", [""])
    
    # Special case for the user's specific set code if it's still wrong
    for item in data["stored_items"]:
        if "7512 TCR + 7514 MB + 7513" in item.get("search_code", ""):
            item["images"] = ["/static/images/Aquant/7512TCR+7514MB+7513TCR.png"]
    
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Total fixed: {total}")

if __name__ == "__main__":
    fix_page_70_all()
