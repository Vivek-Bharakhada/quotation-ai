import sys
import os
import json
import re
import fitz
import glob
from PIL import Image

# Setup paths
STATIC_IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "images")
INDEX_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "search_index_v2.json")

def rebuild_aquant_images():
    print("--- STARTING AQUANT-ONLY IMAGE REBUILD ---")
    
    if not os.path.exists(INDEX_FILE):
        print(f"ERROR: Index file {INDEX_FILE} not found.")
        return

    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    items = data.get("stored_items", [])
    aquant_items = [i for i in items if i.get("brand") == "Aquant"]
    
    if not aquant_items:
        print("No Aquant items found in index.")
        return

    # Find PDF
    pdf_path = r"backend\uploads\Aquant Price List Vol 15. Feb 2026_Searchable.pdf"
    if not os.path.exists(pdf_path):
        # try relative to backend
        pdf_path = r"uploads\Aquant Price List Vol 15. Feb 2026_Searchable.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF not found at {pdf_path}")
        return

    doc = fitz.open(pdf_path)
    os.makedirs(STATIC_IMAGES_DIR, exist_ok=True)

    # 1. Cleanup OLD Aquant images
    for f in os.listdir(STATIC_IMAGES_DIR):
        if f.startswith("Aquant_") and (f.endswith(".jpg") or f.endswith(".png")):
            try:
                os.remove(os.path.join(STATIC_IMAGES_DIR, f))
            except:
                pass

    print(f"Processing {len(aquant_items)} items from Aquant PDF...")
    
    # Simple extraction logic (coordinated with pdf_reader.py heuristics)
    for i, item in enumerate(aquant_items):
        page_num = item.get("page", 1) - 1
        if page_num < 0 or page_num >= len(doc): continue
        
        page = doc[page_num]
        imgs = page.get_images(full=True)
        
        if not imgs: continue
        
        # Proximity matching for images on page
        best_img = None
        best_dist = float('inf')
        
        # Get item center (from pdf_reader indexing)
        cx = item.get("cx", 0)
        cy = item.get("cy", 0)
        
        if cx == 0 and cy == 0: continue

        for img_info in page.get_image_info(xrefs=True):
            ix0, iy0, ix1, iy1 = img_info["bbox"]
            icx, icy = (ix0 + ix1) / 2, (iy0 + iy1) / 2
            
            # Aquant images are usually ABOVE the text, so icy should be < cy
            dist = ((icx - cx)**2 + (icy - cy)**2)**0.5
            if icy > cy + 20: # Image is below text, less likely to be main product image for Aquant
                dist += 200 
            
            if dist < best_dist and dist < 400:
                best_dist = dist
                best_img = img_info

        if best_img:
            xref = best_img["xref"]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            ext = base_image["ext"]
            
            img_filename = f"Aquant_p{page_num+1}_i{xref}.{ext}"
            img_path_full = os.path.join(STATIC_IMAGES_DIR, img_filename)
            
            with open(img_path_full, "wb") as f:
                f.write(image_bytes)
            
            item["images"] = [f"/static/images/{img_filename}"]
        
        if i % 100 == 0:
            print(f"Processed {i}/{len(aquant_items)} items.")

    doc.close()
    
    # Save back
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    
    print("--- AQUANT IMAGE REBUILD COMPLETE ---")

if __name__ == "__main__":
    rebuild_aquant_images()
