import fitz, glob, re

pdf_path = glob.glob('uploads/*.pdf')[0]
doc = fitz.open(pdf_path)
page = doc[7]
raw_blocks = page.get_text("blocks")

text_blocks = []
for b in raw_blocks:
    if b[6] != 0: continue
    text = b[4].strip()
    if len(text) < 5: continue
    text_blocks.append({
        "text": text,
        "bbox": fitz.Rect(b[0], b[1], b[2], b[3])
    })

text_blocks.sort(key=lambda b: (b["bbox"].y0, b["bbox"].x0))

groups = []

def starts_new_product(text):
    first_line = text.split('\n')[0].strip()
    return bool(re.match(r'^([A-Z0-9+]{2,})\s*[-:]', first_line))

for blk in text_blocks:
    added = False
    for group in groups:
        gx0 = min(b["bbox"].x0 for b in group)
        gx1 = max(b["bbox"].x1 for b in group)
        gy0 = min(b["bbox"].y0 for b in group)
        gy1 = max(b["bbox"].y1 for b in group)
        
        vertical_dist = 0
        if blk["bbox"].y0 > gy1: vertical_dist = blk["bbox"].y0 - gy1  
        elif blk["bbox"].y1 < gy0: vertical_dist = gy0 - blk["bbox"].y1 
        
        horiz_dist = 0
        if blk["bbox"].x0 > gx1: horiz_dist = blk["bbox"].x0 - gx1  
        elif blk["bbox"].x1 < gx0: horiz_dist = gx0 - blk["bbox"].x1 
        
        if vertical_dist <= 30 and horiz_dist <= 50:
            if starts_new_product(blk["text"]):
                continue  # don't merge if it's a new product!
            group.append(blk)
            added = True
            break
            
    if not added:
        groups.append([blk])

for i, g in enumerate(groups):
    # Sort blocks within group by y0 to read top-to-bottom
    g.sort(key=lambda b: b["bbox"].y0)
    text = "\n".join(b["text"] for b in g)
    if '9006' in text or '9009' in text:
        print(f"--- GROUP {i} ---")
        print(text)
