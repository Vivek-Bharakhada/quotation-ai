import fitz
import re
import os

pdf_path = r'c:\Users\DELL\OneDrive\Desktop\AIML Project\quotation-ai\backend\uploads\Aquant Price List Vol. 14 Feb. 2025 - Low Res Searchable.pdf'
doc = fitz.open(pdf_path)

def is_product_code(text):
    t = text.strip()
    words = t.split()
    if not words: return False
    w = words[0]
    if w.isdigit() and 4 <= len(w) <= 7: return True
    if re.match(r'^[A-Z]{1,3}-\d+', w): return True
    if re.match(r'^\d{3,}-[A-Z]', w): return True
    return False

def is_header(text):
    lines = text.strip().split('\n')
    for t in lines:
        t = t.strip()
        if not t or len(t) < 4: continue
        if any(c.isdigit() for c in t): continue
        letters = [c for c in t if c.isalpha()]
        if not letters: continue
        upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
        if upper_ratio > 0.8 and len(t) >= 5:
            return t
    return None

def is_price_line(text):
    return "MRP" in text or '`' in text or '₹' in text

import json

for p_num in range(3, 8):
    page = doc[p_num]
    print(f"--- PAGE {p_num + 1} ---")
    
    img_records = []
    for img_index, img in enumerate(page.get_images(full=True)):
        xref = img[0]
        width, height = img[2], img[3]
        if width < 50 or height < 50: continue
        try:
            rects = page.get_image_rects(xref)
            if rects: img_records.append(rects[0])
        except: pass
    
    blocks = page.get_text("blocks")
    page_products = []
    current_category = "UNKNOWN"
    
    for b in blocks:
        if b[6] != 0: continue # Only text
        
        x0, y0, x1, y1 = b[:4]
        text = b[4].strip()
        
        if not text: continue
        
        h = is_header(text)
        if h:
            current_category = h
            continue
            
        has_code = is_product_code(text)
        has_price = is_price_line(text)
        
        if not has_code and not has_price:
            continue
            
        # extract price
        price = "0"
        price_match = re.search(r'MRP\s*[`:₹\s]*([\d,]+)', text, re.IGNORECASE) or \
                      re.search(r'[`₹]\s*([\d,]{3,})', text)
        if price_match:
            price = price_match.group(1).replace(",", "")
            
        name = text.split('\n')[0].strip()
        
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        
        page_products.append({
            "name": name,
            "text": text,
            "price": price,
            "cx": cx,
            "cy": cy,
            "images": []
        })

    # Image matching
    used_img = set()
    for prod in page_products:
        best_img = None
        best_dist = float('inf')
        
        for i, ir in enumerate(img_records):
            if i in used_img: continue
            
            img_cx = (ir.x0 + ir.x1) / 2
            img_cy = (ir.y0 + ir.y1) / 2
            
            dx = abs(img_cx - prod['cx'])
            dy = img_cy - prod['cy']
            
            v_penalty = 0
            if dy > 50: v_penalty = 200 # Image below text is less common
            if dy < -300: v_penalty = 150 # Too far above
            
            dist = (dx**2 + dy**2)**0.5 + v_penalty
            if dist < best_dist and dist < 800:
                best_dist = dist
                best_img = i
                
        if best_img is not None:
            prod['images'].append(f"img_{best_img}")
            used_img.add(best_img)

    for p in page_products:
        print(json.dumps({
            "name": p["name"],
            "price": p["price"],
            "images": p["images"]
        }, indent=2))
