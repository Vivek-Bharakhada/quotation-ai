import fitz
import os
import json

PDF_PATH = r"c:\Movies\quotation-ai\quotation-ai\backend\uploads\Aquant Price List Vol 15. Feb 2026_Searchable.pdf"
IMG_ROOT = r"c:\Movies\quotation-ai\quotation-ai\backend\static\images\Aquant"
INDEX_PATH = r"c:\Movies\quotation-ai\quotation-ai\backend\search_index_v2.json"

def fix_7512_sets():
    doc = fitz.open(PDF_PATH)
    page = doc[70] # Page 71
    
    images = page.get_images(full=True)
    all_extracted = []
    for img in images:
        xref = img[0]
        rects = page.get_image_rects(xref)
        if not rects: continue
        r = rects[0]
        # Middle row
        if 320 < r.y0 < 340:
            base_image = doc.extract_image(xref)
            all_extracted.append({
                "rect": r,
                "bytes": base_image["image"]
            })
    
    # Sort by X
    all_extracted.sort(key=lambda x: x["rect"].x0)
    
    print(f"Found {len(all_extracted)} images for 7512 sets")
    
    # Codes in order on page:
    codes = [
        "7512 MI + 7514 MB + 7513 MI",
        "7512 MG + 7514 MB + 7513 MG",
        "7512 TCR + 7514 MB + 7513", # This is the code in index
        "7512 OG + 7514 MB + 7513 OG"
    ]
    
    with open(INDEX_PATH, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    
    fixed = 0
    for i, img_info in enumerate(all_extracted):
        if i >= len(codes): break
        code = codes[i]
        
        # Clean filename
        filename = code.replace(" ", "") + ".png"
        filepath = os.path.join(IMG_ROOT, filename)
        with open(filepath, "wb") as f:
            f.write(img_info["bytes"])
        
        for item in data["stored_items"]:
            if item.get("search_code") == code:
                item["images"] = [f"/static/images/Aquant/{filename}"]
                fixed += 1
                print(f"Fixed {code} -> {filename}")
                break
    
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Total fixed: {fixed}")

if __name__ == "__main__":
    fix_7512_sets()
