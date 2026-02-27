import fitz
import os
import re

import glob
pdf_path = glob.glob('uploads/*.pdf')[0]
doc = fitz.open(pdf_path)

page = doc[7] # page 8
raw_blocks = page.get_text("blocks")
text_blocks = []
for b in raw_blocks:
    if b[6] != 0: continue
    text_blocks.append({"text": b[4], "bbox": fitz.Rect(b[0], b[1], b[2], b[3])})

for gap in [2, 5, 8, 10]:
    groups = []
    current = []
    last_y1 = None
    for blk in text_blocks:
        if last_y1 is None or blk["bbox"].y0 - last_y1 <= gap:
            current.append(blk)
        else:
            if current: groups.append(current)
            current = [blk]
        last_y1 = blk["bbox"].y1
    if current: groups.append(current)
    
    # how many groups contain 9006, 9009?
    print(f"Gap: {gap}, Total groups: {len(groups)}")
    for g in groups:
        text = "\n".join([b['text'] for b in g])
        if "9006" in text or "9009" in text:
            print("--- GROUP ---")
            print(text.strip())
    print("\n")
