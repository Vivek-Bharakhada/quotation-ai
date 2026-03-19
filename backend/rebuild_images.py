import os
import json
import re
import fitz
import glob
from PIL import Image
import io

# Setup paths
STATIC_IMAGES_DIR = "static/images"
INDEX_FILE = "search_index_v2.json"

if not os.path.exists(STATIC_IMAGES_DIR):
    os.makedirs(STATIC_IMAGES_DIR)

# Get PDF paths
pdfs = glob.glob('uploads/*.pdf')
aquant_pdf = next((p for p in pdfs if 'aquant' in p.lower()), None)
kohler_pdf = next((p for p in pdfs if 'kohler' in p.lower()), None)

# Load JSON
with open(INDEX_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)
items = data.get("stored_items", [])

# Clear static/images correctly
for f in os.listdir(STATIC_IMAGES_DIR):
    if f.endswith(".jpg") or f.endswith(".png"):
        try:
            os.remove(os.path.join(STATIC_IMAGES_DIR, f))
        except:
            pass

docs = {}
if aquant_pdf: docs["aquant"] = fitz.open(aquant_pdf)
if kohler_pdf: docs["kohler"] = fitz.open(kohler_pdf)

def _clean_model(text):
    m = re.search(r'\((.*?)\)', text)
    if m:
        base = m.group(1).strip()
    else:
        m2 = re.search(r'^[A-Z0-9\-]+', text)
        base = m2.group(0).strip() if m2 else text.strip()
    return re.sub(r'[^a-zA-Z0-9]+', '_', base).strip('_').lower()

def _get_page_images(page):
    img_records = []
    for img_info in page.get_images(full=True):
        xref = img_info[0]
        rects = page.get_image_rects(xref)
        if not rects: continue
        rect = rects[0]
        # Capture smaller product icons too
        if rect.width < 30 or rect.height < 30 or rect.width > 500 or rect.height > 750:
            continue
        # Allow more flexible aspect ratios for flat items
        if rect.width / max(1, rect.height) > 6 or rect.height / max(1, rect.width) > 6:
            continue
            
        img_records.append({"xref": xref, "rect": rect})
    return img_records

print(f"Starting precise extraction for {len(items)} items...")

total_updated = 0

for item in items:
    src = item.get("source", "").lower()
    brand = "aquant" if "aquant" in src else "kohler" if "kohler" in src else None
    
    # We only redo aquant & kohler
    if not brand or brand not in docs:
        if brand != "plumber": # keeping plumber cover logic intact (just clearing images makes plumber blank which is better than logo)
            item["images"] = []
        continue
        
    page_num = item.get("page", 1) - 1
    model_raw = item.get("name", "")
    model_code = _clean_model(model_raw)
    
    if not model_code or len(model_code) < 2:
        item["images"] = []
        continue

    doc = docs[brand]
    if page_num < 0 or page_num >= doc.page_count:
        item["images"] = []
        continue
        
    page = doc[page_num]
    
    # Extract blocks to find product text
    blocks = page.get_text("blocks")
    target_cx, target_cy = None, None
    
    # Clean up model code for searching inside PDF text
    search_term = model_code.upper()
    if brand == "kohler" and search_term.startswith("K_"):
        search_term = search_term[2:]
    search_term = search_term.split('_')[0]
    
    # Fallback: if search_term (from code) isn't found, try name words for non-standard items
    tokens = [w.upper() for w in model_raw.split() if len(w) > 3][:3]
    
    for b in blocks:
        t = b[4].strip().upper()
        if not t: continue
        
        # Priority 1: Model Code match
        match = (search_term in t) or (model_raw.split()[0].upper() in t)
        
        # Priority 2: Full Name word match fallback (important for cleaners/kits)
        if not match and tokens:
            match = all(tok in t for tok in tokens)
            
        # Priority 3: First 2 words match (very soft fallback for cleaners)
        if not match and len(tokens) >= 2:
            match = all(tok in t for tok in tokens[:2])
            
        # Priority 4: ANY token match (Ultra-loose for Page 166 cleaners)
        if not match and page_num == 165 and tokens:
            match = any(tok in t for tok in tokens)
            
        if match:
            target_cx = (b[0] + b[2]) / 2
            target_cy = (b[1] + b[3]) / 2
            break
            
    if target_cx is None:
        item["images"] = []
        continue
        
    # Get good image candidates
    candidates = _get_page_images(page)
    if not candidates:
        item["images"] = []
        continue
        
    # Strictly match nearest image
    best_xref = None
    best_dist = float('inf')
    
    for c in candidates:
        r = c["rect"]
        img_cx, img_cy = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2
        
        dx = abs(img_cx - target_cx)
        dy = img_cy - target_cy
        
        # Grid layout check: vertical alignment (same row) is primary for tables.
        # We still use a weighted dx to prefer direct alignment, but we allow 
        # wide-column matches if they are vertically clean.
        
        row_bonus = 0
        if abs(dy) < 60: row_bonus = -2000 # Significant bonus for being in the same row
        
        col_penalty = 0
        # If very far (>350px), it might be a different section, so keep some penalty
        if dx > 450: col_penalty = 1500 
            
        v_penalty = 0
        # If image is çok far above/below (>500px), it's probably not related
        if dy > 500: v_penalty = 2000
        if dy < -700: v_penalty = 2000
        
        # Weighted distance with row bonus
        dist = ((dx * 5)**2 + dy**2)**0.5 + col_penalty + v_penalty + row_bonus
        
        if dist < best_dist and dist < 8000:
            best_dist = dist
            best_xref = c["xref"]
            
    if best_xref:
        # Extract and save it
        img_file = f"{brand}_{model_code}.jpg"
        abs_img_path = os.path.join(STATIC_IMAGES_DIR, img_file)
        
        if not os.path.exists(abs_img_path):
            try:
                # Find the rect for this xref again to make sure we use the correct one
                rects = page.get_image_rects(best_xref)
                if rects:
                    r = rects[0]
                    # RENDER the exact portion of the page where the image is.
                    # This handles cropping correctly if the PDF uses a tiled image resource.
                    pix = page.get_pixmap(clip=r, dpi=150)
                    pix.save(abs_img_path)
            except Exception as e:
                print(f"Failed to render image for {model_code}: {e}")
                
        if os.path.exists(abs_img_path):
            item["images"] = [f"/static/images/{img_file}"]
            total_updated += 1
        else:
            item["images"] = []
    else:
        item["images"] = []

# Save JSON
with open(INDEX_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)

print(f"Properly extracted and assigned exactly {total_updated} accurate images with model numbers!")
