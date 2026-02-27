import fitz, glob

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

# We'll just build groups incrementally
groups = []

for blk in text_blocks:
    added = False
    for group in groups:
        gx0 = min(b["bbox"].x0 for b in group)
        gx1 = max(b["bbox"].x1 for b in group)
        gy0 = min(b["bbox"].y0 for b in group)
        gy1 = max(b["bbox"].y1 for b in group)
        
        vertical_dist = 0
        if blk["bbox"].y0 > gy1: vertical_dist = blk["bbox"].y0 - gy1  # blk is below
        elif blk["bbox"].y1 < gy0: vertical_dist = gy0 - blk["bbox"].y1 # blk is above
        else: vertical_dist = 0 # overlapping vertically
        
        horiz_dist = 0
        if blk["bbox"].x0 > gx1: horiz_dist = blk["bbox"].x0 - gx1  # blk is to the right
        elif blk["bbox"].x1 < gx0: horiz_dist = gx0 - blk["bbox"].x1 # blk is to the left
        else: horiz_dist = 0 # overlapping horizontally
        
        # If they are close vertically AND horizontally, merge them.
        # "Close horizontally" means overlapping or very small gap
        if vertical_dist <= 30 and horiz_dist <= 40:
            group.append(blk)
            added = True
            break
            
    if not added:
        groups.append([blk])

print(f"Total groups: {len(groups)}")
for i, g in enumerate(groups):
    text = "\n".join(b["text"] for b in g)
    if '9006' in text or '9009' in text:
        print(f"--- GROUP {i} ---")
        gx0 = min(b["bbox"].x0 for b in g)
        gy0 = min(b["bbox"].y0 for b in g)
        print(f"x0={gx0:.1f}, y0={gy0:.1f}")
        print(text)
        print()
