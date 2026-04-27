import fitz
import os
import json

PDF_PATH = r"c:\Movies\quotation-ai\quotation-ai\backend\uploads\Aquant Price List Vol 15. Feb 2026_Searchable.pdf"
IMG_ROOT = r"c:\Movies\quotation-ai\quotation-ai\backend\static\images\Aquant"
INDEX_PATH = r"c:\Movies\quotation-ai\quotation-ai\backend\search_index_v2.json"

def fix_page_68_high_res():
    doc = fitz.open(PDF_PATH)
    page = doc[67] # Page 68
    
    # Coordinates from previous check:
    # Row 1 (7008): y0 ~ 45
    # Row 2 (7009): y0 ~ 366
    
    # Define boxes for each product
    # RG (Left): x0 < 200
    # GG (Middle): 200 < x0 < 400
    # BG (Right): x0 > 400
    
    products = [
        {"code": "7008 RG ORY", "rect": fitz.Rect(16, 45, 191, 356)},
        {"code": "7008 GG ORY", "rect": fitz.Rect(210, 45, 385, 351)},
        {"code": "7008 BG ORY", "rect": fitz.Rect(404, 45, 579, 356)},
        {"code": "7009 RG + 9245 CM OASIS GRACE", "rect": fitz.Rect(16, 366, 192, 677)},
        {"code": "7009 GG + 9245 CM OASIS GRACE", "rect": fitz.Rect(210, 366, 386, 677)},
        {"code": "7009 BG + 9245 CM OASIS GRACE", "rect": fitz.Rect(404, 366, 579, 677)},
    ]
    
    with open(INDEX_PATH, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    
    for p in products:
        code = p["code"]
        r = p["rect"]
        
        # Increase resolution for better quality
        pix = page.get_pixmap(clip=r, matrix=fitz.Matrix(2, 2))
        filename = code.replace(" ", "") + ".png"
        filepath = os.path.join(IMG_ROOT, filename)
        pix.save(filepath)
        print(f"Saved {filename}")
        
        # Update index
        for item in data["stored_items"]:
            if item.get("search_code", "").upper() == code.upper():
                item["images"] = [f"/static/images/Aquant/{filename}"]
                print(f"Mapped {code}")
                break
                
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    fix_page_68_high_res()
