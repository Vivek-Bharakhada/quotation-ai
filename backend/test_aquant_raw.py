import fitz, os
import re

pdf_path = os.path.join("uploads", "Aquant Price List Vol. 14 Feb. 2025 - Low Res Searchable.pdf")
doc = fitz.open(pdf_path)

print("Processing pages 10-12")
for page_num in range(10, 13):
    page = doc[page_num]
    d = page.get_text("dict")
    print(f"--- PAGE {page_num} ---")
    
    raw_lines = []
    for block in d.get("blocks", []):
        if block.get("type", -1) == 0:  # text block
            for line in block.get("lines", []):
                text = "".join(span.get("text", "") for span in line.get("spans", [])).strip()
                if len(text) < 2: continue
                bbox = line["bbox"]
                raw_lines.append({
                    "text": text,
                    "y0": bbox[1],
                    "x0": bbox[0],
                })
    
    raw_lines.sort(key=lambda l: (round(l["y0"] / 5), l["x0"]))
    for line in raw_lines:
        print(f"y: {line['y0']:.1f}, x: {line['x0']:.1f} | {line['text']}")
    print()
