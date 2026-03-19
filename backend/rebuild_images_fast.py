"""
Optimized Image Extraction - Accurate Matching
Uses the stable image extraction but improves text matching
"""

import os
import json
import re
import fitz
import glob

STATIC_IMAGES_DIR = "static/images"
INDEX_FILE = "search_index_v2.json"

if not os.path.exists(STATIC_IMAGES_DIR):
    os.makedirs(STATIC_IMAGES_DIR)

pdfs = glob.glob('uploads/*.pdf')
aquant_pdf = next((p for p in pdfs if 'aquant' in p.lower()), None)
kohler_pdf = next((p for p in pdfs if 'kohler' in p.lower()), None)

# Clear images
for f in os.listdir(STATIC_IMAGES_DIR):
    if f.endswith((".jpg", ".png")):
        try:
            os.remove(os.path.join(STATIC_IMAGES_DIR, f))
        except:
            pass

with open(INDEX_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)
items = data.get("stored_items", [])

docs = {}
if aquant_pdf: 
    docs["aquant"] = fitz.open(aquant_pdf)
if kohler_pdf: 
    docs["kohler"] = fitz.open(kohler_pdf)

print(f"Processing {len(items)} items...")

def extract_code(text):
    """Extract product code"""
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Match product codes: 9272, K-28362, etc
        if re.match(r'^[A-Z0-9\-]+\s', line) or re.match(r'^\d{4,}[A-Z]?\s', line):
            return line.split()[0]
    return None

def get_images_with_positions(page):
    """Get image info with safer error handling"""
    images = []
    try:
        for img_data in page.get_images(full=True):
            try:
                xref = img_data[0]
                w, h = img_data[2], img_data[3]
                
                # Filter by size
                if w < 25 or h < 25 or w > 700 or h > 850:
                    continue
                
                ratio = w / max(1, h)
                if ratio > 7 or ratio < 0.14:
                    continue
                
                # Get rectangle position
                rects = page.get_image_rects(xref)
                if rects:
                    r = rects[0]
                    images.append({
                        'xref': xref,
                        'rect': r,
                        'cx': (r.x0 + r.x1) / 2,
                        'cy': (r.y0 + r.y1) / 2,
                    })
            except:
                continue
    except:
        pass
    
    return images

def find_text_position(page, search_code):
    """Find product code position in page"""
    blocks = page.get_text("blocks")
    for b in blocks:
        if b[6] != 0:
            continue
        text = str(b[4]).strip().upper()
        if not text:
            continue
        
        # Check if search code is in first line
        first_line = text.split('\n')[0]
        if search_code and search_code.upper() in first_line:
            x0, y0, x1, y1 = b[:4]
            return {
                'cx': (x0 + x1) / 2,
                'cy': (y0 + y1) / 2,
                'y0': y0,
                'y1': y1,
                'x0': x0,
                'x1': x1,
                'text': first_line[:80]
            }
    
    return None

def score_image_match(prod_pos, img_info, page_width):
    """Score image-to-product match"""
    if not prod_pos:
        return float('inf')
    
    p_cx, p_cy = prod_pos['cx'], prod_pos['cy']
    i_cx, i_cy = img_info['cx'], img_info['cy']
    
    # Distance calculation
    dx = abs(i_cx - p_cx)
    dy = i_cy - p_cy
    
    # Column match bonus
    p_col = 0 if p_cx < page_width / 2 else 1
    i_col = 0 if i_cx < page_width / 2 else 1
    col_bonus = 0 if p_col == i_col else 200
    
    # Vertical alignment
    # Prefer image slightly above, same row, or slightly below
    v_penalty = 0
    if dy < -600:
        v_penalty = 1200
    elif dy < -300:
        v_penalty = 400
    elif dy > 400:
        v_penalty = 1000
    elif dy > 100:
        v_penalty = 300
    
    # Combined score
    dist = ((dx * 3) ** 2 + dy ** 2) ** 0.5 + col_bonus + v_penalty
    
    # Reject very far matches
    if dist > 900:
        return float('inf')
    
    return dist

total = 0
for i, item in enumerate(items):
    src = item.get("source", "").lower()
    brand = "aquant" if "aquant" in src else "kohler" if "kohler" in src else None
    
    if not brand or brand not in docs:
        item["images"] = []
        continue
    
    page_num = item.get("page", 1) - 1
    name = item.get("name", "")
    
    if not name or page_num < 0:
        item["images"] = []
        continue
    
    doc = docs[brand]
    if page_num >= len(doc):
        item["images"] = []
        continue
    
    page = doc[page_num]
    code = extract_code(name)
    
    if not code:
        item["images"] = []
        continue
    
    # Find product position
    prod_pos = find_text_position(page, code)
    if not prod_pos:
        item["images"] = []
        continue
    
    # Get images  
    images = get_images_with_positions(page)
    if not images:
        item["images"] = []
        continue
    
    # Find best image
    best_img = None
    best_score = float('inf')
    
    for img in images:
        score = score_image_match(prod_pos, img, page.rect.width)
        if score < best_score:
            best_score = score
            best_img = img
    
    if best_img:
        try:
            filename = f"{brand}_p{page_num+1}_{best_img['xref']}.jpg"
            filepath = os.path.join(STATIC_IMAGES_DIR, filename)
            
            if not os.path.exists(filepath):
                pix = page.get_pixmap(clip=best_img['rect'], dpi=180)
                pix.save(filepath)
                pix = None
            
            if os.path.exists(filepath):
                item["images"] = [f"/static/images/{filename}"]
                total += 1
            else:
                item["images"] = []
        except Exception as e:
            item["images"] = []
    else:
        item["images"] = []
    
    if (i + 1) % 200 == 0:
        print(f"Progress: {i+1}/{len(items)} - Success: {total}")

# Save
with open(INDEX_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)

print(f"\n✓ Completed! Successfully matched {total} accurate product images!")
