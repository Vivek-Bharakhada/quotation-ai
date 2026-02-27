import fitz, os, re

pdf_path = os.path.join("uploads", "Aquant Price List Vol. 14 Feb. 2025 - Low Res Searchable.pdf")
doc = fitz.open(pdf_path)

def clean_text(text):
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    text = re.sub(r'(?<=[A-Za-z0-9])-(?=[A-Z])', ' - ', text)
    # Also replace fancy dashes with regular dash for simplicity
    text = re.sub(r'[\u2013\u2014]', '-', text)
    return text.strip()

def starts_new_product(text_line):
    if "MRP" in text_line: return False
    # Use standard hyphen since clean_text normalizes them
    return bool(re.match(r'^([A-Z0-9+]{2,}(?:\s+[a-zA-Z0-9+]+)*)\s*[-:]', text_line))

page = doc[10]
d = page.get_text("dict")

raw_lines = []
for block in d.get("blocks", []):
    if block.get("type", -1) == 0: 
        for line in block.get("lines", []):
            text = "".join(span.get("text", " ") for span in line.get("spans", [])).strip()
            text = clean_text(text)
            if len(text) < 2: continue
            raw_lines.append({
                "text": text,
                "bbox": fitz.Rect(line["bbox"])
            })

raw_lines.sort(key=lambda l: (round(l["bbox"].y0 / 5), l["bbox"].x0))

groups = []
with open("grouping_log4.txt", "w", encoding="utf-8") as f:
    for line in raw_lines:
        best_group = None
        best_score = float('inf')
        
        for group in groups:
            gy0 = min(b["bbox"].y0 for b in group)
            gy1 = max(b["bbox"].y1 for b in group)
            vertical_overlap = min(line["bbox"].y1, gy1) - max(line["bbox"].y0, gy0)
            
            vertical_dist = 0
            if line["bbox"].y0 > gy1: vertical_dist = line["bbox"].y0 - gy1  
            elif line["bbox"].y1 < gy0: vertical_dist = gy0 - line["bbox"].y1 
            
            gx1 = max(b["bbox"].x1 for b in group)
            gx0 = min(b["bbox"].x0 for b in group)
            
            horiz_dist = 0
            if line["bbox"].x0 > gx1: horiz_dist = line["bbox"].x0 - gx1
            elif line["bbox"].x1 < gx0: horiz_dist = gx0 - line["bbox"].x1
            
            same_row = vertical_overlap > -5
            close_vertically = vertical_dist <= 25 and horiz_dist < 150
            
            is_new_prod = starts_new_product(line["text"])
            has_prod = any(starts_new_product(b["text"]) for b in group)
            
            if same_row or close_vertically:
                if is_new_prod and has_prod:
                    continue
                if vertical_dist > 35:
                    continue
                if not same_row and horiz_dist > 80:
                    continue
                    
                score = vertical_dist * 2 + horiz_dist
                if score < best_score:
                    best_score = score
                    best_group = group
                    
        if best_group is not None:
            best_group.append(line)
        else:
            groups.append([line])

    for i, g in enumerate(groups):
        f.write(f"--- GROUP {i} ---\n")
        max_words = 0
        for b in g:
            f.write(f"{b['text']}\n")
