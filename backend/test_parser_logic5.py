import fitz, os, re

pdf_path = os.path.join("uploads", "Aquant Price List Vol. 14 Feb. 2025 - Low Res Searchable.pdf")
doc = fitz.open(pdf_path)

def clean_text(text):
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    text = re.sub(r'(?<=[A-Za-z0-9])-(?=[A-Z])', ' - ', text)
    return text.strip()

def starts_new_product(text_line):
    if "MRP" in text_line: return False
    return bool(re.match(r'^([A-Z0-9+]{2,}(?:\s+[a-zA-Z0-9]+)*)\s*[-:]', text_line))

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

with open("grouping_log3.txt", "w", encoding="utf-8") as f:
    for line in raw_lines:
        is_new_prod = starts_new_product(line["text"])
        f.write(f"Line: {line['text']} | is_new_prod: {is_new_prod}\n")
