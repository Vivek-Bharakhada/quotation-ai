import os, sys
sys.path.insert(0, '.')
import fitz
import pdf_reader
import re

def is_product_code(text):
    t = text.strip()
    words = t.split()
    if not words: return False
    w = words[0]
    if w.isdigit() and 4 <= len(w) <= 7: return True
    if re.match(r'^[A-Z]{1,3}-\d+', w): return True
    if re.match(r'^\d{3,}-[A-Z]', w): return True
    return False

files = [f for f in os.listdir('uploads') if 'Aquant' in f and f.endswith('.pdf')]
path = os.path.join('uploads', files[0])
doc = fitz.open(path)
page_num = 3 # Page 4
page = doc[page_num]

print(f"--- IMAGES ON PAGE {page_num+1} ---")
for i, img in enumerate(page.get_images()):
    xref = img[0]
    rects = page.get_image_rects(xref)
    if rects:
        r = rects[0]
        cx = (r.x0 + r.x1)/2
        cy = (r.y0 + r.y1)/2
        print(f"Img {i} (xref {xref}): rect={r}, cx={cx:.1f}, cy={cy:.1f}")

print(f"\n--- TEXT LINES ON PAGE {page_num+1} ---")
d = page.get_text("dict")
for block in d["blocks"]:
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            txt = span["text"].strip()
            if txt:
                bbox = fitz.Rect(span["bbox"])
                cx = (bbox.x0 + bbox.x1)/2
                cy = (bbox.y0 + bbox.y1)/2
                marker = " [CODE]" if is_product_code(txt) else ""
                print(f"Line: '{txt[:30]}' {marker} cx={cx:.1f}, cy={cy:.1f}")
doc.close()
