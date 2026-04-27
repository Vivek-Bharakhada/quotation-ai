import fitz
import os
import json

PDF_PATH = r"c:\Movies\quotation-ai\quotation-ai\backend\uploads\Aquant Price List Vol 15. Feb 2026_Searchable.pdf"
IMG_ROOT = r"c:\Movies\quotation-ai\quotation-ai\backend\static\images\Aquant"
INDEX_PATH = r"c:\Movies\quotation-ai\quotation-ai\backend\search_index_v2.json"

def fix_page_68_colors():
    doc = fitz.open(PDF_PATH)
    page = doc[67] # Page 68
    
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
    # Row 1 (7008): Y ~ 53
    # Row 2 (7009): Y ~ 434
    
    row_7008 = sorted([i for i in all_extracted if 40 < i["rect"].y0 < 80], key=lambda x: x["rect"].x0)
    row_7009 = sorted([i for i in all_extracted if 360 < i["rect"].y0 < 400], key=lambda x: x["rect"].x0)
    
    print(f"Found 7008: {len(row_7008)}, 7009: {len(row_7009)}")
    
    with open(INDEX_PATH, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    
    colors = ["RG", "GG", "BG"]
    
    def update_index(img_list, base_code_template, color_list):
        fixed = 0
        for i, img_info in enumerate(img_list):
            if i >= len(color_list): break
            color = color_list[i]
            
            # Construct the code as it appears in the index
            # The template might need adjustment
            if "7008" in base_code_template:
                code = f"7008 {color} ORY"
            else:
                # 7009 RG + 9245 CM OASIS GRACE
                code = f"7009 {color} + 9245 CM OASIS GRACE"
                
            filename = code.replace(" ", "") + ".png"
            filepath = os.path.join(IMG_ROOT, filename)
            
            with open(filepath, "wb") as f:
                f.write(img_info["bytes"])
            
            # Update index
            found = False
            for item in data["stored_items"]:
                if item.get("search_code", "").upper() == code.upper():
                    item["images"] = [f"/static/images/Aquant/{filename}"]
                    fixed += 1
                    found = True
                    print(f"Fixed {code} -> {filename}")
                    break
            
            if not found:
                print(f"Could not find {code} in index")
        return fixed

    total = 0
    total += update_index(row_7008, "7008 {COLOR} ORY", colors)
    total += update_index(row_7009, "7009 {COLOR} + 9245 CM OASIS GRACE", colors)
    
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Total fixed: {total}")

if __name__ == "__main__":
    fix_page_68_colors()
