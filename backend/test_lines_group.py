import fitz, glob, re

pdf_path = glob.glob('uploads/*.pdf')[0]
doc = fitz.open(pdf_path)
page = doc[7]
d = page.get_text("dict")

raw_lines = []
for block in d["blocks"]:
    if block["type"] == 0:
        for line in block["lines"]:
            text = "".join(span["text"] for span in line["spans"]).strip()
            if len(text) < 2: continue
            raw_lines.append({
                "text": text,
                "bbox": fitz.Rect(line["bbox"])
            })

# Sort lines top-to-bottom, left-to-right
raw_lines.sort(key=lambda l: (round(l["bbox"].y0 / 5), l["bbox"].x0))

groups = []

def starts_new_product(text):
     return bool(re.match(r'^([A-Z0-9+]{2,})\s*[-:]', text))

for line in raw_lines:
    added = False
    
    # Try to find a group to add the line to
    # We add to the LAST group that matches, to keep reading order
    for i in range(len(groups)-1, -1, -1):
        group = groups[i]
        gx0 = min(b["bbox"].x0 for b in group)
        gx1 = max(b["bbox"].x1 for b in group)
        gy0 = min(b["bbox"].y0 for b in group)
        gy1 = max(b["bbox"].y1 for b in group)
        
        vertical_dist = 0
        if line["bbox"].y0 > gy1: vertical_dist = line["bbox"].y0 - gy1  
        elif line["bbox"].y1 < gy0: vertical_dist = gy0 - line["bbox"].y1 
        
        horiz_dist = 0
        if line["bbox"].x0 > gx1: horiz_dist = line["bbox"].x0 - gx1  
        elif line["bbox"].x1 < gx0: horiz_dist = gx0 - line["bbox"].x1 
        
        # Merge if it's close vertically and in the same column (small horizontal dist)
        if vertical_dist <= 25 and horiz_dist <= 50:
            if starts_new_product(line["text"]):
                # NEVER merge if this line is obviously a new product code
                continue
            group.append(line)
            added = True
            break
            
    if not added:
        groups.append([line])

for i, g in enumerate(groups):
    text = "\n".join(b["text"] for b in g)
    if '9006' in text or '9009' in text or '9010HO' in text:
        print(f"--- GROUP {i} ---")
        gx0 = min(b["bbox"].x0 for b in g)
        gy0 = min(b["bbox"].y0 for b in g)
        print(f"y0={gy0:.1f}, x0={gx0:.1f}")
        print(text)
        print()
