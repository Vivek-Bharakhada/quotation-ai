import fitz, os, io, re, json
from PIL import Image

doc = fitz.open('uploads/Aquant Price List Vol 15. Feb 2026_Searchable.pdf')
page = doc[5]

def is_product_code(text):
    t = text.strip()
    words = t.split()
    if not words: return False
    w = words[0]
    if w.isdigit() and 4 <= len(w) <= 7: return True
    if re.match(r'^[A-Z]{1,3}-\d+', w): return True
    if re.match(r'^\d{3,}-\d+', w): return True
    return False

blocks = page.get_text("blocks")
page_products = []
for b in blocks:
    t = b[4].strip()
    if not t: continue
    if is_product_code(t):
         p = {
             "name": t.splitlines()[0],
             "cx": (b[0] + b[2]) / 2,
             "cy": (b[1] + b[3]) / 2,
             "images": []
         }
         page_products.append(p)

def _get_page_images(page):
    img_records = []
    for img_info in page.get_images(full=True):
        xref = img_info[0]
        rects = page.get_image_rects(xref)
        if not rects: continue
        rect = rects[0]
        if rect.width < 30 or rect.height < 30: continue
        img_records.append({"xref": xref, "rect": rect})
    return img_records

candidates = _get_page_images(page)

print(f"Page 6: Found {len(page_products)} products, {len(candidates)} images.")

for p in page_products:
    target_cx = p["cx"]
    target_cy = p["cy"]
    best_xref = None
    best_dist = float('inf')
    
    for c in candidates:
        r = c["rect"]
        img_cx = (r.x0 + r.x1) / 2
        img_cy = (r.y0 + r.y1) / 2
        
        dx = abs(img_cx - target_cx)
        dy = img_cy - target_cy
        
        col_penalty = 0
        if dx > 400: col_penalty = 1000
            
        v_penalty = 0
        if dy > 300: v_penalty = 800
        if dy < -500: v_penalty = 800
        
        dist = (dx**2 + dy**2)**0.5 + col_penalty + v_penalty
        
        if dist < best_dist and dist < 800:
            best_dist = dist
            best_xref = c["xref"]
            
    print(f"Product: {p['name']} (at {target_cx:.0f}, {target_cy:.0f}) -> xref={best_xref} (dist={best_dist:.1f})")
