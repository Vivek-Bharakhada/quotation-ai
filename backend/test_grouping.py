import fitz, glob, os, re

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

text_blocks.sort(key=lambda b: b["bbox"].y0)

groups = []
current_group = []
last_y1 = None
GROUP_GAP = 30

def starts_new_product(text):
    # Check if text starts with something like "9006 -", "K-1234", etc.
    first_line = text.split('\n')[0].strip()
    # A product typically starts with 3+ alphanumeric/dash chars then space-hyphen
    return bool(re.match(r'^([A-Z0-9+]{2,})\s*[-:]', first_line))

for blk in text_blocks:
    if not current_group:
        current_group.append(blk)
    else:
        gap = blk["bbox"].y0 - last_y1
        
        # Merge if gap <= GROUP_GAP AND the new block DOES NOT explicitly start a new product
        if gap <= GROUP_GAP and not starts_new_product(blk["text"]):
            current_group.append(blk)
        else:
            groups.append(current_group)
            current_group = [blk]
    last_y1 = blk["bbox"].y1

if current_group:
    groups.append(current_group)

for i, g in enumerate(groups):
    text = "\n".join([b["text"] for b in g])
    if '9006' in text or '9009' in text:
        print(f"--- GROUP {i} ---")
        print(text)
        
        # Also let's see its mid-point compared to all images on the page
        group_y_mid = (g[0]["bbox"].y0 + g[-1]["bbox"].y1) / 2
        group_x_mid = (g[0]["bbox"].x0 + g[-1]["bbox"].x1) / 2
        
        # Find images on page
        image_list = page.get_images(full=True)
        img_rects = []
        for img_index, img in enumerate(image_list):
            xref = img[0]
            try:
                rects = page.get_image_rects(xref)
                if rects: img_rects.append((f"i{img_index}", rects[0]))
            except: pass
            
        best_img = None
        best_dist = float('inf')
        for name, r in img_rects:
            img_cy = (r.y0 + r.y1)/2
            img_cx = (r.x0 + r.x1)/2
            dist = ((img_cx - group_x_mid)**2 + (img_cy - group_y_mid)**2)**0.5
            if dist < best_dist:
                best_dist = dist
                best_img = name
                
        print(f"Nearest image: {best_img} at distance {best_dist:.1f}")
