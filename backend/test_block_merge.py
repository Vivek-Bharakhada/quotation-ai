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

def is_price_line(text):
    return "MRP" in text or '`' in text or '₹' in text

print("--- PAGE 4 Merge Test ---")
page = doc[3]
blocks = [b for b in page.get_text("blocks") if b[6] == 0]

# Sort blocks top-to-bottom, left-to-right (roughly)
# Actually, let's group by X column first.
col_dividers = [0, 200, 400, 800] # Approximate
def get_col(x):
    for i in range(len(col_dividers) - 1):
        if col_dividers[i] <= x < col_dividers[i + 1]: return i
    return 0

products = []
for b in blocks:
    x0, y0, x1, y1 = b[:4]
    text = b[4].strip().replace('\u0003', ' ')
    if len(text) < 5: continue
    if "STONE WASH BASINS" in text.upper(): continue
    if "COLLECTION" in text.upper() and len(text) < 50: continue
    
    col = get_col(x0)
    
    # Try attaching to last product in same column
    attached = False
    for prod in reversed(products):
        if prod['col'] != col: continue
        
        vertical_gap = y0 - prod['y1']
        
        # If it's a new product code, DO NOT attach UNLESS the previous one has no code
        if is_product_code(text) and prod['has_code'] and vertical_gap > 10:
            continue
            
        if 0 <= vertical_gap <= 80:
            prod['text'] += "\n" + text
            prod['y1'] = max(prod['y1'], y1)
            prod['x0'] = min(prod['x0'], x0)
            prod['x1'] = max(prod['x1'], x1)
            prod['has_code'] = prod['has_code'] or is_product_code(text)
            attached = True
            break
            
    if not attached:
        products.append({
            'col': col,
            'text': text,
            'has_code': is_product_code(text),
            'y0': y0,
            'y1': y1,
            'x0': x0,
            'x1': x1
        })

import json
for p in products:
    price = "0"
    price_match = re.search(r'MRP\s*[`:₹\s]*([\d,]+)', p['text'], re.IGNORECASE) or \
                  re.search(r'[`₹]\s*([\d,]{3,})', p['text'])
    if price_match:
        price = price_match.group(1).replace(",", "")
        
    print(json.dumps({
        "name": p['text'].split('\n')[0][:50],
        "price": price,
        "valid": is_product_code(p['text']) or is_price_line(p['text'])
    }, indent=2))
