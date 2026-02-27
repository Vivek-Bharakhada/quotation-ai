import fitz, glob, re

pdf_path = glob.glob('uploads/*.pdf')[0]
doc = fitz.open(pdf_path)
page = doc[9] # page 10 (0-indexed)

d = page.get_text("dict")
raw_lines = []
for block in d.get("blocks", []):
    if block.get("type", -1) == 0:
        for line in block.get("lines", []):
            text = "".join(span.get("text", "") for span in line.get("spans", [])).strip()
            if len(text) < 2: continue
            raw_lines.append({
                "text": text,
                "bbox": fitz.Rect(line["bbox"])
            })

raw_lines.sort(key=lambda l: (round(l["bbox"].y0 / 5), l["bbox"].x0))

starts = [i for i, l in enumerate(raw_lines) if '7006 GG' in l["text"]]
if starts:
    idx = starts[0]
    print(f"Found 7006 GG at index {idx}")
    for i in range(idx, min(idx+10, len(raw_lines))):
        print(f"[{i}] {raw_lines[i]['bbox']}, text: {raw_lines[i]['text']}")
