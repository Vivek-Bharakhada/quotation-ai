"""
Improved Image Extraction with Better Matching Algorithm
- Fuzzy text matching
- Smarter proximity scoring  
- Better image filtering
- Detailed logging
"""

import os
import json
import re
import fitz
import glob
from PIL import Image
import difflib

# Setup paths
STATIC_IMAGES_DIR = "static/images"
INDEX_FILE = "search_index_v2.json"

if not os.path.exists(STATIC_IMAGES_DIR):
    os.makedirs(STATIC_IMAGES_DIR)

# Get PDF paths
pdfs = glob.glob('uploads/*.pdf')
aquant_pdf = next((p for p in pdfs if 'aquant' in p.lower()), None)
kohler_pdf = next((p for p in pdfs if 'kohler' in p.lower()), None)

print(f"Aquant PDF: {aquant_pdf}")
print(f"Kohler PDF: {kohler_pdf}")

# Load JSON
with open(INDEX_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)
items = data.get("stored_items", [])

# Clear static/images
for f in os.listdir(STATIC_IMAGES_DIR):
    if f.endswith(".jpg") or f.endswith(".png"):
        try:
            os.remove(os.path.join(STATIC_IMAGES_DIR, f))
        except:
            pass

docs = {}
if aquant_pdf: docs["aquant"] = fitz.open(aquant_pdf)
if kohler_pdf: docs["kohler"] = fitz.open(kohler_pdf)

def extract_product_code(text):
    """Extract main product code from text"""
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        # Match patterns: 9272, K-28362IN, 1234-5, etc
        match = re.search(r"^([A-Z0-9\-]+)", line)
        if match:
            code = match.group(1).strip()
            if len(code) >= 4:
                return code
    return None

def extract_tokens(text):
    """Extract meaningful tokens from product name"""
    # Remove price patterns
    text = re.sub(r'MRP.*|₹.*|\d{4,}.*', '', text, flags=re.IGNORECASE)
    # Split into words
    words = re.findall(r'[A-Z0-9]+', text.upper())
    return [w for w in words if len(w) > 2]

def text_similarity(text1, text2):
    """Calculate similarity between two texts"""
    return difflib.SequenceMatcher(None, text1.upper(), text2.upper()).ratio()

def get_all_text_blocks(page):
    """Get all text blocks from page with their positions"""
    blocks = page.get_text("blocks")
    text_blocks = []
    for b in blocks:
        if b[6] != 0:  # Skip non-text blocks
            continue
        x0, y0, x1, y1 = b[:4]
        text = str(b[4]).strip()
        if text:
            text_blocks.append({
                'text': text,
                'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1,
                'cx': (x0 + x1) / 2, 'cy': (y0 + y1) / 2
            })
    return text_blocks

def find_product_block(page, search_code, search_tokens):
    """Find the product block on page using better matching"""
    text_blocks = get_all_text_blocks(page)
    
    candidates = []
    for block in text_blocks:
        text_upper = block['text'].upper()
        
        # Priority 1: Exact code match in first line
        first_line = block['text'].split('\n')[0].upper()
        if search_code and search_code.upper() in first_line:
            candidates.append((100, block, 'exact_code'))
            
        # Priority 2: Fuzzy code match
        if search_code and search_code.upper() in text_upper:
            sim = text_similarity(search_code, text_upper)
            candidates.append((80 + int(sim * 20), block, 'fuzzy_code'))
            
        # Priority 3: All tokens match
        if all(tok in text_upper for tok in search_tokens):
            candidates.append((70, block, 'all_tokens'))
            
        # Priority 4: Most tokens match
        if search_tokens:
            matches = sum(1 for tok in search_tokens if tok in text_upper)
            if matches >= len(search_tokens) * 0.7:
                candidates.append((60 + matches * 5, block, 'most_tokens'))
    
    if candidates:
        # Return best match
        candidates.sort(reverse=True, key=lambda x: x[0])
        return candidates[0][1]
    
    return None

def get_page_images(page):
    """Get all images on page with sizes"""
    img_records = []
    try:
        for img_info in page.get_images(full=True):
            xref = img_info[0]
            width, height = img_info[2], img_info[3]
            
            # More lenient filtering on raw dimensions
            if width < 20 or height < 20:
                continue
            if width > 800 or height > 1000:
                continue
            
            # Skip very wide or very tall images
            ratio = width / max(1, height)
            if ratio > 8 or ratio < 0.125:
                continue
            
            # Try to get rect info
            try:
                rects = page.get_image_rects(xref)
                if not rects:
                    continue
                rect = rects[0]
            except:
                # Fallback: estimate rect from dimensions
                # This is a safety net in case get_image_rects fails
                continue
            
            img_records.append({
                'xref': xref,
                'rect': rect,
                'width': rect.width,
                'height': rect.height,
                'cx': (rect.x0 + rect.x1) / 2,
                'cy': (rect.y0 + rect.y1) / 2
            })
    except:
        pass
    
    return img_records

def find_best_image(product_block, images_on_page, page_width):
    """Find best matching image for product"""
    if not images_on_page or not product_block:
        return None
    
    p_cx = product_block['cx']
    p_cy = product_block['cy']
    p_col = 0 if p_cx < page_width / 2 else 1
    
    best_img = None
    best_score = float('inf')
    
    for img in images_on_page:
        img_cx = img['cx']
        img_cy = img['cy']
        img_col = 0 if img_cx < page_width / 2 else 1
        
        # Calculate distance
        dx = abs(img_cx - p_cx)
        dy = img_cy - p_cy
        
        # Scoring penalties
        # Same column preference (big bonus if same column)
        col_penalty = 0 if p_col == img_col else 300
        
        # Vertical alignment preference
        # Images slightly above or in same row are best
        v_penalty = 0
        if dy > 300:  # Image far below
            v_penalty = 800
        elif dy > 80:  # Image some distance below
            v_penalty = 200
        elif dy < -500:  # Image far above
            v_penalty = 800
        elif dy < -200:  # Image some distance above
            v_penalty = 100
        else:
            v_penalty = 0  # Good vertical alignment
        
        # Horizontal distance
        h_dist = dx * 0.5  # Weight horizontal less than vertical
        
        # Total distance with penalties
        total_dist = h_dist + v_penalty + col_penalty + (dx ** 2 + dy ** 2) ** 0.5 * 0.1
        
        if total_dist < best_score and total_dist < 1000:
            best_score = total_dist
            best_img = img
    
    return best_img

print(f"\nStarting improved image extraction for {len(items)} items...")
print("=" * 80)

total_updated = 0
total_no_match = 0
total_no_image = 0

for idx, item in enumerate(items):
    src = item.get("source", "").lower()
    brand = "aquant" if "aquant" in src else "kohler" if "kohler" in src else None
    
    if not brand or brand not in docs:
        item["images"] = []
        continue
    
    page_num = item.get("page", 1) - 1
    product_name = item.get("name", "").strip()
    
    if not product_name:
        item["images"] = []
        continue
    
    doc = docs[brand]
    if page_num < 0 or page_num >= doc.page_count:
        item["images"] = []
        continue
    
    page = doc[page_num]
    page_width = page.rect.width
    
    # Extract search terms
    search_code = extract_product_code(product_name)
    search_tokens = extract_tokens(product_name)
    
    # Find product block on PDF
    product_block = find_product_block(page, search_code, search_tokens)
    
    if not product_block:
        item["images"] = []
        total_no_match += 1
        continue
    
    # Get all images on page
    page_images = get_page_images(page)
    
    if not page_images:
        item["images"] = []
        total_no_image += 1
        continue
    
    # Find best image match
    best_img = find_best_image(product_block, page_images, page_width)
    
    if not best_img:
        item["images"] = []
        total_no_image += 1
        continue
    
    # Extract and save image
    try:
        img_file = f"{brand}_p{page_num+1}_{best_img['xref']}.jpg"
        abs_img_path = os.path.join(STATIC_IMAGES_DIR, img_file)
        
        if not os.path.exists(abs_img_path):
            pix = page.get_pixmap(clip=best_img['rect'], dpi=200)
            pix.save(abs_img_path)
            pix = None
        
        if os.path.exists(abs_img_path):
            item["images"] = [f"/static/images/{img_file}"]
            total_updated += 1
            if (idx + 1) % 100 == 0:
                print(f"Progress: {idx+1}/{len(items)} - Updated: {total_updated}")
        else:
            item["images"] = []
    except Exception as e:
        print(f"Error extracting image for {product_name}: {e}")
        item["images"] = []

# Save JSON
with open(INDEX_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)

print("\n" + "=" * 80)
print(f"✓ Successfully extracted: {total_updated} images")
print(f"✗ No matching product block: {total_no_match}")
print(f"✗ No images found on page: {total_no_image}")
print(f"✗ Failed or skipped: {len(items) - total_updated - total_no_match - total_no_image}")
print("=" * 80)
