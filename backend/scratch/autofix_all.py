"""
AUTO-FIX SCRIPT — All 3 Problems
1. Price = 0  → Extract from Kohler PDF
2. Image file missing on disk → Fix path
3. No image entry → Find image on disk or assign PDF page image
"""
import json, sys, os, re
sys.stdout.reconfigure(encoding='utf-8')

INDEX_PATH = r'C:\Movies\quotation-ai\quotation-ai\backend\search_index_v2.json'
PDF_PATH   = os.path.join(r'C:\Movies\quotation-ai\quotation-ai\backend\uploads', "Kohler_Pricebook (March'26).pdf")
STATIC_ROOT = r'C:\Movies\quotation-ai\quotation-ai\backend'
KOHLER_IMG_DIR = r'C:\Movies\quotation-ai\quotation-ai\backend\static\images\Kohler'
AQUANT_IMG_DIR = r'C:\Movies\quotation-ai\quotation-ai\backend\static\images\Aquant'

print("Loading index...")
with open(INDEX_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)
stored = data['stored_items']
print(f"Total items: {len(stored)}")

# ============================================================
# FIX 1: Price = 0 → Extract from PDF
# ============================================================
print("\n" + "="*60)
print("FIX 1: Extracting prices from Kohler PDF for price=0 items")
print("="*60)

import pdfplumber

# Build a price map from PDF: code -> price
pdf_price_map = {}

print("Scanning PDF for prices...")
with pdfplumber.open(PDF_PATH) as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        if not text:
            continue
        lines = text.split('\n')
        for j, line in enumerate(lines):
            # Look for K-XXXXXX pattern with MRP on same or adjacent line
            codes = re.findall(r'K-[\w\d]+-[\w\d-]+', line)
            for code in codes:
                code = code.strip().rstrip('.')
                # Check current line for price
                price_match = re.search(r'(?:MRP[^\d]*|`\s*)(\d[\d,]+)', line)
                if price_match:
                    price_str = price_match.group(1).replace(',', '')
                    pdf_price_map[code.upper()] = price_str
                else:
                    # Check next few lines
                    for k in range(1, 4):
                        if j + k < len(lines):
                            next_line = lines[j + k]
                            pm = re.search(r'(?:MRP[^\d]*|`\s*)(\d[\d,]+)', next_line)
                            if pm:
                                price_str = pm.group(1).replace(',', '')
                                pdf_price_map[code.upper()] = price_str
                                break

print(f"PDF price map built: {len(pdf_price_map)} codes found")

# Apply prices to price=0 items
fix1_count = 0
fix1_not_found = []

for i, item in enumerate(stored):
    price = str(item.get('price', '0')).strip()
    if price not in ['0', '', 'None', 'null', '0.0']:
        continue

    code = (item.get('search_code') or item.get('base_code') or '').upper().strip()
    full_code = (item.get('full_code') or '').upper().strip()

    found_price = None
    for lookup in [code, full_code]:
        if lookup in pdf_price_map:
            found_price = pdf_price_map[lookup]
            break
        # Try without trailing chars
        clean = lookup.rstrip('.')
        if clean in pdf_price_map:
            found_price = pdf_price_map[clean]
            break

    if found_price:
        stored[i]['price'] = found_price
        stored[i]['source'] = "Kohler_Pricebook (March'26)"
        fix1_count += 1
        print(f"  ✅ [{i:04d}] {code} → ₹{found_price}")
    else:
        fix1_not_found.append((i, code, item.get('brand','')))

print(f"\nFIX 1 DONE: {fix1_count} prices updated")
print(f"Still not found in PDF: {len(fix1_not_found)}")
for i, code, brand in fix1_not_found:
    print(f"  ❌ [{i:04d}] [{brand}] {code}")

# ============================================================
# FIX 2: Image file missing on disk → Fix path
# ============================================================
print("\n" + "="*60)
print("FIX 2: Fixing broken image paths")
print("="*60)

fix2_count = 0
for i, item in enumerate(stored):
    imgs = item.get('images', [])
    if not imgs:
        continue
    img_rel = imgs[0].lstrip('/')
    full_path = os.path.join(STATIC_ROOT, img_rel)
    if os.path.exists(full_path):
        continue

    # Try to find correct image for this item
    code = (item.get('search_code') or item.get('base_code') or '').strip()
    brand = item.get('brand', '')

    img_dir = KOHLER_IMG_DIR if brand == 'Kohler' else AQUANT_IMG_DIR

    # Try clean code as filename
    found_img = None
    for ext in ['.png', '.jpg', '.jpeg', '.webp']:
        candidate = os.path.join(img_dir, code + ext)
        if os.path.exists(candidate):
            rel = '/static/images/' + ('Kohler' if brand == 'Kohler' else 'Aquant') + '/' + code + ext
            found_img = rel
            break

    if found_img:
        stored[i]['images'] = [found_img]
        fix2_count += 1
        print(f"  ✅ [{i:04d}] {code} → {found_img}")
    else:
        # Try removing parentheses from existing path
        orig = imgs[0]
        clean_name = re.sub(r'\([^)]+\)', '', os.path.basename(orig)).strip()
        for ext in ['.png', '.jpg', '.jpeg']:
            clean_base = os.path.splitext(clean_name)[0]
            candidate = os.path.join(img_dir, clean_base + ext)
            if os.path.exists(candidate):
                rel = '/static/images/' + ('Kohler' if brand == 'Kohler' else 'Aquant') + '/' + clean_base + ext
                stored[i]['images'] = [rel]
                fix2_count += 1
                print(f"  ✅ [{i:04d}] {code} → {rel} (cleaned path)")
                break
        else:
            print(f"  ❌ [{i:04d}] {code} — no image found on disk (orig: {orig})")

print(f"\nFIX 2 DONE: {fix2_count} image paths fixed")

# ============================================================
# FIX 3: No image entry → Find image on disk
# ============================================================
print("\n" + "="*60)
print("FIX 3: Assigning images to items with no image")
print("="*60)

fix3_count = 0
for i, item in enumerate(stored):
    if item.get('images') and item['images'] != []:
        continue

    code = (item.get('search_code') or item.get('base_code') or '').strip()
    brand = item.get('brand', '')
    img_dir = KOHLER_IMG_DIR if brand == 'Kohler' else AQUANT_IMG_DIR
    brand_slug = 'Kohler' if brand == 'Kohler' else 'Aquant'

    found_img = None

    # Try exact code match
    for ext in ['.png', '.jpg', '.jpeg', '.webp']:
        candidate = os.path.join(img_dir, code + ext)
        if os.path.exists(candidate):
            found_img = f'/static/images/{brand_slug}/{code}{ext}'
            break

    # Try base part of code (before space)
    if not found_img:
        base = code.split(' ')[0]
        for ext in ['.png', '.jpg', '.jpeg']:
            candidate = os.path.join(img_dir, base + ext)
            if os.path.exists(candidate):
                found_img = f'/static/images/{brand_slug}/{base}{ext}'
                break

    # Try fuzzy match — check if any file starts with base code number
    if not found_img:
        base_num = re.sub(r'[^0-9]', '', code.split(' ')[0])[:4]
        if base_num and os.path.exists(img_dir):
            for fname in os.listdir(img_dir):
                fname_num = re.sub(r'[^0-9]', '', fname)[:4]
                if fname_num == base_num and fname.lower().endswith(('.png', '.jpg', '.jpeg')):
                    found_img = f'/static/images/{brand_slug}/{fname}'
                    break

    if found_img:
        stored[i]['images'] = [found_img]
        fix3_count += 1
        print(f"  ✅ [{i:04d}] {code} → {found_img}")
    else:
        print(f"  ❌ [{i:04d}] [{brand}] {code} — no image found")

print(f"\nFIX 3 DONE: {fix3_count} images assigned")

# ============================================================
# SAVE
# ============================================================
print("\n" + "="*60)
print("Saving updated index...")
with open(INDEX_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)
print("✅ search_index_v2.json saved!")

# Final summary
remaining_zero = sum(1 for it in stored if str(it.get('price','0')).strip() in ['0','','None','null'])
remaining_no_img = sum(1 for it in stored if not it.get('images') or it.get('images') == [])
print(f"\n📊 FINAL STATE:")
print(f"  Price = 0 remaining : {remaining_zero}")
print(f"  No image remaining  : {remaining_no_img}")
